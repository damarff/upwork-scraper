"""Scrape individual job detail pages (Upwork).

Improved approach:
1. Try __NUXT__ state (works for search, limited for detail)
2. Fallback: parse rendered HTML with BeautifulSoup
3. Extract by content sections, not fragile CSS class names
"""

import re
import time
from typing import Optional

from bs4 import BeautifulSoup

from src.scrapers.base import BaseScraper, wait_for_page, POST_RENDER_DELAY
from src.utils.logger import info, warn, error


class JobDetailScraper(BaseScraper):
    """Scrape full details from a single Upwork job page."""

    def platform(self) -> str:
        return "upwork"

    def search_keyword(self, keyword: str) -> list[dict]:
        raise NotImplementedError("Use scrape_job_detail() instead")

    def _parse_html(self, html: str) -> dict:
        """Extract job data from rendered HTML."""
        soup = BeautifulSoup(html, "html.parser")

        result = {
            "title": "",
            "description": "",
            "budget": "N/A",
            "budget_type": "",
            "duration": "",
            "experience_level": "",
            "hours": "",
            "skills": [],
            "client": {},
            "proposals": "",
            "url": "",
        }

        # ── Title (extract BEFORE removing anything!) ──
        h1 = soup.find("h1")
        if h1:
            result["title"] = h1.get_text(strip=True)

        # ── Hapus noise ──
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        # Hapus header TAPI jangan kalo isinya h1 (title ada di header)
        for header in soup.find_all("header"):
            if not header.find("h1"):
                header.decompose()

        # ── Cari deskripsi ──
        # Coba class .job-details (existing di halaman baru)
        job_details = soup.find(class_=lambda c: c and "job-details" in c if c else False)
        if job_details:
            result["description"] = job_details.get_text(separator="\n", strip=True)
        else:
            # Fallback: ambil body, cari "Summary" atau "About"
            body = soup.find("body")
            if body:
                text = body.get_text(separator="\n", strip=True)
                # Cari mulai dari "Summary" atau "About this project"
                for marker in ["Summary", "About this project", "Project Description", "Description"]:
                    idx = text.find(marker)
                    if idx >= 0:
                        # Ambil 5000 chars setelah marker
                        result["description"] = text[idx:idx+5000]
                        break
                if not result["description"]:
                    result["description"] = text[:5000]

        # ── Budget & metadata ──
        raw_text = soup.get_text(separator=" ", strip=True)  # case-sensitive for $
        body_text = raw_text.lower()

        # Budget amount — cari pola $XXX + type
        # Hapus angka besar (total spent, dll) dari pertimbangan
        clean_text = re.sub(r'\$[\d,.]+(?:K|M|B|k|million|billion)', '', raw_text)
        
        fp_match = re.search(r'\$([\d,]+(?:\.\d{2})?)\s*(?:fixed[- ]?price|fixed)', clean_text, re.IGNORECASE)
        hl_match = re.search(r'\$([\d,]+(?:\.\d{2})?)\s*(?:hourly|/hr)', clean_text, re.IGNORECASE)
        
        if fp_match:
            result["budget"] = f"${fp_match.group(1)}"
            result["budget_type"] = "fixed"
        elif hl_match:
            result["budget"] = f"${hl_match.group(1)}/hr"
            result["budget_type"] = "hourly"
        else:
            # Cari $XXX aja (tapi bukan angka besar kayak total spent)
            any_dollar = re.findall(r'\$([\d,]+(?:\.\d{2})?)', clean_text)
            if any_dollar:
                for d in any_dollar:
                    num = float(d.replace(",", ""))
                    if 10 <= num <= 50000:
                        result["budget"] = f"${d}"
                        break
            
            # Type fallback
            if "fixed-price" in body_text or "fixed price" in body_text:
                result["budget_type"] = "fixed"
            elif "hourly" in body_text:
                result["budget_type"] = "hourly"

        # Duration
        dur_match = re.search(r'(\d+\s*-\s*\d+\s*(months?|weeks?|days?))', body_text)
        if dur_match:
            result["duration"] = dur_match.group(1)
        elif re.search(r'(more than\s+\d+\s*(months?|weeks?))', body_text):
            m = re.search(r'(more than\s+\d+\s*(months?|weeks?))', body_text)
            if m:
                result["duration"] = m.group(1)

        # Experience level — cari di sekitar kata "experience" atau "level"
        exp_section = re.search(r'(experience\s*level|level)[\s\S]{0,100}(entry|intermediate|expert)', body_text, re.IGNORECASE)
        if exp_section:
            result["experience_level"] = exp_section.group(2).lower()

        # Hours per week
        hrs_match = re.search(r'(\d+\s*-\s*\d+\s*hrs?/week)', body_text)
        if hrs_match:
            result["hours"] = hrs_match.group(1)
        else:
            hrs_match = re.search(r'(more than\s+\d+\s*hrs?/week)', body_text)
            if hrs_match:
                result["hours"] = hrs_match.group(1)

        # ── Skills ──
        skills_section = soup.find(
            lambda tag: tag.name in ["div", "section"] and
            tag.get_text(strip=True).lower().startswith("skills")
        )
        if not skills_section:
            for heading in soup.find_all(["h2", "h3", "h4", "strong", "span"]):
                if "skill" in heading.get_text(strip=True).lower():
                    skills_section = heading.find_parent(["div", "section"])
                    break

        if skills_section:
            skills_text = skills_section.get_text(strip=True)
            for marker in ["mandatory skills", "preferred qualifications", "nice-to-have skills"]:
                idx = skills_text.lower().find(marker)
                if idx >= 0:
                    skills_text = skills_text[idx:]
                    break
            # Ambil baris yang mirip skill (bukan kalimat panjang)
            raw_skills = [s.strip() for s in skills_text.replace("Nice-to-have skills", "\n").replace("Mandatory skills", "\n").split("\n") if s.strip()]
            result["skills"] = [s for s in raw_skills if len(s) < 50 and not any(x in s.lower() for x in ["skills", "expertise", "qualification"])]

        # ── Client info ──
        client_section = soup.find(
            lambda tag: tag.name in ["div", "section"] and
            "about the client" in tag.get_text(strip=True).lower()
        )
        if client_section:
            client_text = client_section.get_text(strip=True)
            result["client"]["raw"] = client_text[:1000]
            # Extract rating
            rating = re.search(r'rating is ([\d.]+)', client_text, re.IGNORECASE)
            if rating:
                result["client"]["rating"] = rating.group(1)
            # Total spent
            spent = re.search(r'\$[\d,.]+k?\s*total spent', client_text, re.IGNORECASE)
            if spent:
                result["client"]["total_spent"] = spent.group(0)
            # Hires
            hires = re.search(r'(\d+)\s*hires', client_text, re.IGNORECASE)
            if hires:
                result["client"]["hires"] = hires.group(1)
            # Member since
            member = re.search(r'member since\s*([A-Za-z]+\s+\d{1,2},?\s*\d{4})', client_text, re.IGNORECASE)
            if member:
                result["client"]["member_since"] = member.group(1).strip()
            # Country
            countries = [
                "united kingdom", "united states", "australia", "canada",
                "germany", "france", "india", "morocco", "netherlands"
            ]
            for c in countries:
                if c in client_text.lower():
                    result["client"]["country"] = c.title()
                    break

        # ── Proposals count ──
        prop_match = re.search(r'(?:proposals?\s*[:\-]?\s*)(\d+\s*to\s*\d+|\d+\s*-\s*\d+|\d+)',
                               body_text, re.IGNORECASE)
        if prop_match:
            result["proposals"] = prop_match.group(1)

        return result

    def scrape_job_detail(self, url: str) -> Optional[dict]:
        """Get full job detail from an Upwork job URL."""
        info(f"Fetching job detail: {url}")

        self.page.get(url)
        wait_for_page(self.page)
        time.sleep(POST_RENDER_DELAY)

        # Coba NUXT dulu (mungkin masih ada data walau terbatas)
        try:
            nuxt = self.page.run_js("return window.__NUXT__")
            if nuxt:
                info("__NUXT__ found, checking for job data...")
        except Exception:
            pass

        # Parsing HTML
        try:
            html = self.page.html
            result = self._parse_html(html)
            result["url"] = url

            info(f"Extracted: {result['title'][:60]}")
            return result

        except Exception as e:
            error(f"Failed to scrape job detail: {e}", url=url)
            return None

    def scrape_all(self, keywords=None) -> list:
        raise NotImplementedError("Use scrape_job_detail() for individual jobs")
