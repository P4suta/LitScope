"""Tests for text normalizer."""

import pytest

from litscope.ingestion.text_normalizer import (
    NormalizedChapter,
    NormalizedSentence,
    NormalizedToken,
    TextNormalizer,
    _is_transformer_model,
    _load_spacy_model,
)


@pytest.fixture(scope="module")
def normalizer() -> TextNormalizer:
    return TextNormalizer()


class TestTextNormalizer:
    def test_strip_html(self, normalizer: TextNormalizer) -> None:
        html = "<html><body><p>Hello <b>world</b>.</p></body></html>"
        result = normalizer.normalize(html)
        assert result.sentences
        assert "<" not in result.sentences[0].text

    def test_sentences_extracted(self, normalizer: TextNormalizer) -> None:
        html = "<p>First sentence. Second sentence.</p>"
        result = normalizer.normalize(html)
        assert result.sent_count >= 2

    def test_tokens_have_pos(self, normalizer: TextNormalizer) -> None:
        html = "<p>The cat sat on the mat.</p>"
        result = normalizer.normalize(html)
        tokens = result.sentences[0].tokens
        pos_tags = {t.pos for t in tokens}
        assert len(pos_tags) > 1

    def test_tokens_have_lemma(self, normalizer: TextNormalizer) -> None:
        html = "<p>The dogs were running quickly.</p>"
        result = normalizer.normalize(html)
        lemmas = {t.lemma for t in result.sentences[0].tokens}
        assert "dog" in lemmas

    def test_space_tokens_filtered(self, normalizer: TextNormalizer) -> None:
        html = "<p>Hello   world.</p>"
        result = normalizer.normalize(html)
        for sent in result.sentences:
            assert all(t.text.strip() for t in sent.tokens)

    def test_empty_sentences_filtered(self, normalizer: TextNormalizer) -> None:
        html = "<p>   </p><p>Real sentence here.</p>"
        result = normalizer.normalize(html)
        for sent in result.sentences:
            assert sent.tokens

    def test_unicode_normalization(self, normalizer: TextNormalizer) -> None:
        # NFKC normalizes ﬁ ligature to "fi"
        html = "<p>The ﬁrst oﬃce.</p>"
        result = normalizer.normalize(html)
        text = " ".join(t.text for sent in result.sentences for t in sent.tokens)
        assert "fi" in text

    def test_word_count(self, normalizer: TextNormalizer) -> None:
        html = "<p>One two three.</p>"
        result = normalizer.normalize(html)
        assert result.word_count >= 3

    def test_chapter_sent_count(self, normalizer: TextNormalizer) -> None:
        html = "<p>Sentence one. Sentence two.</p>"
        result = normalizer.normalize(html)
        assert result.sent_count >= 2

    def test_sentence_char_count(self, normalizer: TextNormalizer) -> None:
        html = "<p>Hello world.</p>"
        result = normalizer.normalize(html)
        assert result.sentences[0].char_count > 0

    def test_is_stop_annotation(self, normalizer: TextNormalizer) -> None:
        html = "<p>The cat is on the mat.</p>"
        result = normalizer.normalize(html)
        stop_tokens = [t for t in result.sentences[0].tokens if t.is_stop]
        assert len(stop_tokens) > 0


class TestTextNormalizerInit:
    def test_custom_nlp_injection(self) -> None:
        """Passing a custom nlp skips the default spaCy load."""
        import spacy

        custom_nlp = spacy.load("en_core_web_sm", exclude=["ner", "parser"])
        custom_nlp.enable_pipe("senter")
        norm = TextNormalizer(nlp=custom_nlp)
        result = norm.normalize("<p>Hello world.</p>")
        assert result.sent_count >= 1

    def test_explicit_model_name(self) -> None:
        """Passing model_name loads that specific model."""
        norm = TextNormalizer(model_name="en_core_web_sm")
        result = norm.normalize("<p>Hello world.</p>")
        assert result.sent_count >= 1

    def test_default_uses_settings(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without nlp or model_name, loads from config.spacy_model."""
        from unittest.mock import patch

        import spacy

        loaded_models: list[str] = []
        original_load = spacy.load

        def tracking_load(name: str, **kwargs):  # type: ignore[no-untyped-def]
            loaded_models.append(name)
            return original_load(name, **kwargs)

        monkeypatch.setenv("LITSCOPE_SPACY_MODEL", "en_core_web_sm")
        # Clear cached settings so env var takes effect
        from litscope.config import get_settings

        get_settings.cache_clear()
        try:
            with patch("spacy.load", side_effect=tracking_load):
                TextNormalizer()
            assert loaded_models == ["en_core_web_sm"]
        finally:
            get_settings.cache_clear()


class TestIsTransformerModel:
    def test_trf_suffix_returns_true(self) -> None:
        assert _is_transformer_model("en_core_web_trf") is True

    def test_non_trf_suffix_returns_false(self) -> None:
        assert _is_transformer_model("en_core_web_md") is False

    def test_sm_model_returns_false(self) -> None:
        assert _is_transformer_model("en_core_web_sm") is False


class TestLoadSpacyModel:
    def test_trf_model_excludes_ner_only(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_nlp = MagicMock()
        with (
            patch("spacy.load", return_value=mock_nlp) as mock_load,
            patch("spacy.prefer_gpu"),
        ):
            result = _load_spacy_model("en_core_web_trf")
        mock_load.assert_called_once_with("en_core_web_trf", exclude=["ner"])
        assert result is mock_nlp
        mock_nlp.enable_pipe.assert_not_called()

    def test_trf_model_calls_prefer_gpu(self) -> None:
        from unittest.mock import MagicMock, patch

        with (
            patch("spacy.load", return_value=MagicMock()) as _,
            patch("spacy.prefer_gpu") as mock_gpu,
        ):
            _load_spacy_model("en_core_web_trf")
        mock_gpu.assert_called_once()

    def test_non_trf_excludes_ner_parser_enables_senter(self) -> None:
        from unittest.mock import MagicMock, patch

        mock_nlp = MagicMock()
        with patch("spacy.load", return_value=mock_nlp) as mock_load:
            result = _load_spacy_model("en_core_web_md")
        mock_load.assert_called_once_with(
            "en_core_web_md", exclude=["ner", "parser"]
        )
        mock_nlp.enable_pipe.assert_called_once_with("senter")
        assert result is mock_nlp

    def test_trf_missing_dependency_error(self) -> None:
        from unittest.mock import patch

        with (
            patch("spacy.load", side_effect=OSError("not found")),
            patch("spacy.prefer_gpu"),
            pytest.raises(OSError, match="Failed to load transformer model"),
        ):
            _load_spacy_model("en_core_web_trf")


class TestNormalizedDataclasses:
    def test_normalized_token(self) -> None:
        t = NormalizedToken(text="cat", lemma="cat", pos="NOUN", is_stop=False)
        assert t.text == "cat"
        assert t.pos == "NOUN"

    def test_normalized_sentence_empty(self) -> None:
        s = NormalizedSentence(text="")
        assert s.word_count == 0
        assert s.char_count == 0

    def test_normalized_chapter_empty(self) -> None:
        ch = NormalizedChapter()
        assert ch.word_count == 0
        assert ch.sent_count == 0
