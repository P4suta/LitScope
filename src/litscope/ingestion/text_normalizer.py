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


def _is_transformer_model(name: str) -> bool:
    """Check if the model name refers to a transformer-based model."""
    return name.endswith("_trf")


def _load_spacy_model(name: str) -> Language:
    """Load a spaCy model with appropriate pipeline configuration."""
    if _is_transformer_model(name):
        spacy.prefer_gpu()  # type: ignore[attr-defined]
        try:
            return spacy.load(name, exclude=["ner"])
        except OSError as e:
            msg = (
                f"Failed to load transformer model '{name}'. "
                f"Install with: pip install litscope[hq] && "
                f"python -m spacy download {name}"
            )
            raise OSError(msg) from e
    nlp = spacy.load(name, exclude=["ner", "parser"])
    nlp.enable_pipe("senter")
    return nlp


class TextNormalizer:
    """Normalizes HTML content into structured sentences and tokens."""

    def __init__(
        self, nlp: Language | None = None, model_name: str | None = None
    ) -> None:
        if nlp is not None:
            self._nlp = nlp
            return
        from litscope.config import get_settings

        name = model_name or get_settings().spacy_model
        self._nlp = _load_spacy_model(name)

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
