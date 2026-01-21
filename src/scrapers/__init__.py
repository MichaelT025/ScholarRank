"""Scrapers package for fetching scholarship data from various sources."""

from src.scrapers.base import BaseScraper
from src.scrapers.careeronestop import CareerOneStopScraper
from src.scrapers.fastweb import FastwebScraper
from src.scrapers.iefa import IEFAScraper
from src.scrapers.intl_scholarships import InternationalScholarshipsComScraper
from src.scrapers.scholars4dev import Scholars4devScraper
from src.scrapers.scholarships_com import ScholarshipsComScraper

__all__ = ["BaseScraper", "CareerOneStopScraper", "FastwebScraper", "IEFAScraper", "InternationalScholarshipsComScraper", "Scholars4devScraper", "ScholarshipsComScraper"]
