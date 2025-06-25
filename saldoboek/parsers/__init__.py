# parsers/__init__.py
"""
Bank parsers package voor verschillende bankformaten
"""
from ..config.bank_parsers import BANK_PARSERS
from .sns_parser import SNSParser
from .rabo_parser import RaboParser

# Dynamisch __all__ maken op basis van config
__all__ = [f"{bank.title()}Parser" for bank in BANK_PARSERS.keys()]
