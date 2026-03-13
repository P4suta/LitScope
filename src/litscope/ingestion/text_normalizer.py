"""Text normalizer using spaCy for sentence splitting and tokenization."""

import unicodedata
from dataclasses import dataclass, field

import spacy
from bs4 import BeautifulSoup
from spacy.language import Language


@dataclass(frozen=True)
class NormalizedToken:
    """A single token with linguistic annotations."""

    text: str
    lemma: str
    pos: str
    is_stop: bool


@dataclass(frozen=True)
class NormalizedSentence:
    """A sentence with its tokens."""

    text: str
    tokens: list[NormalizedToken] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        return len(self.tokens)

    @property
    def char_count(self) -> int:
        return len(self.text)


@dataclass(frozen=True)
class NormalizedChapter:
    """A chapter normalized into sentences and tokens."""

    sentences: list[NormalizedSentence] = field(default_factory=list)

    @property
    def word_count(self) -> int:
        return sum(s.word_count for s in self.sentences)

    @property
    def sent_count(self) -> int:
        return len(self.sentences)


class TextNormalizer:
    """Normalizes HTML content into structured sentences and tokens."""

    def __init__(self, nlp: Language | None = None) -> None:
        if nlp is None:
            nlp = spacy.load("en_core_web_sm", exclude=["ner", "parser"])
            nlp.enable_pipe("senter")
        self._nlp = nlp

    def normalize(self, html_content: str) -> NormalizedChapter:
        """Normalize HTML content into sentences and tokens."""
        text = self._strip_html(html_content)
        text = self._normalize_unicode(text)
        doc = self._nlp(text)
        sentences = [
            sent
            for raw_sent in doc.sents
            if (sent := self._process_sentence(raw_sent)).tokens
        ]
        return NormalizedChapter(sentences=sentences)

    @staticmethod
    def _strip_html(html: str) -> str:
        """Strip HTML tags and return plain text."""
        return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)

    @staticmethod
    def _normalize_unicode(text: str) -> str:
        """Apply NFKC Unicode normalization."""
        return unicodedata.normalize("NFKC", text)

    @staticmethod
    def _process_sentence(sent: spacy.tokens.Span) -> NormalizedSentence:
        """Process a spaCy sentence span into a NormalizedSentence."""
        tokens = [
            NormalizedToken(
                text=t.text,
                lemma=t.lemma_.lower(),
                pos=t.pos_,
                is_stop=t.is_stop,
            )
            for t in sent
            if not t.is_space
        ]
        return NormalizedSentence(text=sent.text.strip(), tokens=tokens)
