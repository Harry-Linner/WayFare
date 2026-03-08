"""Property-based tests for DocumentSegment serialization round-trip

**Validates: Requirements 9.3, 9.4**

This module tests that DocumentSegment objects can be serialized to JSON
and deserialized back without losing any information (round-trip property).
"""

import json
import pytest
from hypothesis import given, strategies as st
from dataclasses import asdict

from wayfare.db import DocumentSegment, BoundingBox


# Custom strategies for generating valid test data
@st.composite
def valid_doc_hash(draw):
    """Generate valid document hash strings (alphanumeric, 32-64 chars)"""
    return draw(st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
        min_size=32,
        max_size=64
    ))


@st.composite
def valid_text(draw):
    """Generate valid text content including Unicode and special characters"""
    return draw(st.text(min_size=1, max_size=500))


@st.composite
def valid_bbox_coordinate(draw):
    """Generate valid bounding box coordinates (positive floats, no NaN/Inf)"""
    return draw(st.floats(
        min_value=0.0,
        max_value=10000.0,
        allow_nan=False,
        allow_infinity=False
    ))


@st.composite
def valid_bbox_dimension(draw):
    """Generate valid bounding box dimensions (positive floats > 0, no NaN/Inf)"""
    return draw(st.floats(
        min_value=0.1,
        max_value=10000.0,
        allow_nan=False,
        allow_infinity=False
    ))


class TestSerializationRoundTrip:
    """Property-based tests for DocumentSegment serialization"""

    # Feature: wayfare-mvp-backend, Property 27: DocumentSegment序列化round-trip
    @given(
        doc_hash=valid_doc_hash(),
        text=valid_text(),
        page=st.integers(min_value=0, max_value=10000),
        x=valid_bbox_coordinate(),
        y=valid_bbox_coordinate(),
        width=valid_bbox_dimension(),
        height=valid_bbox_dimension()
    )
    @pytest.mark.property_test
    def test_document_segment_round_trip(self, doc_hash, text, page, x, y, width, height):
        """For any valid DocumentSegment object, serializing to JSON and deserializing 
        should produce an equivalent object with the same field values.
        
        **Validates: Requirements 9.3, 9.4**
        """
        # Create original object
        segment_id = f"{doc_hash}_{page}_0"
        original = DocumentSegment(
            id=segment_id,
            doc_hash=doc_hash,
            text=text,
            page=page,
            bbox=BoundingBox(x=x, y=y, width=width, height=height)
        )
        
        # Serialize to JSON
        original_dict = asdict(original)
        json_str = json.dumps(original_dict)
        
        # Deserialize from JSON
        deserialized_dict = json.loads(json_str)
        deserialized = DocumentSegment(
            id=deserialized_dict['id'],
            doc_hash=deserialized_dict['doc_hash'],
            text=deserialized_dict['text'],
            page=deserialized_dict['page'],
            bbox=BoundingBox(**deserialized_dict['bbox'])
        )
        
        # Verify equivalence - all fields must match exactly
        assert deserialized.id == original.id, \
            f"ID mismatch: {deserialized.id} != {original.id}"
        assert deserialized.doc_hash == original.doc_hash, \
            f"doc_hash mismatch: {deserialized.doc_hash} != {original.doc_hash}"
        assert deserialized.text == original.text, \
            f"text mismatch: {deserialized.text} != {original.text}"
        assert deserialized.page == original.page, \
            f"page mismatch: {deserialized.page} != {original.page}"
        
        # Verify bbox fields
        assert deserialized.bbox.x == original.bbox.x, \
            f"bbox.x mismatch: {deserialized.bbox.x} != {original.bbox.x}"
        assert deserialized.bbox.y == original.bbox.y, \
            f"bbox.y mismatch: {deserialized.bbox.y} != {original.bbox.y}"
        assert deserialized.bbox.width == original.bbox.width, \
            f"bbox.width mismatch: {deserialized.bbox.width} != {original.bbox.width}"
        assert deserialized.bbox.height == original.bbox.height, \
            f"bbox.height mismatch: {deserialized.bbox.height} != {original.bbox.height}"

    # Feature: wayfare-mvp-backend, Property 27: DocumentSegment序列化round-trip
    @given(
        doc_hash=valid_doc_hash(),
        page=st.integers(min_value=0, max_value=10000),
        x=valid_bbox_coordinate(),
        y=valid_bbox_coordinate(),
        width=valid_bbox_dimension(),
        height=valid_bbox_dimension()
    )
    @pytest.mark.property_test
    def test_empty_text_round_trip(self, doc_hash, page, x, y, width, height):
        """Test round-trip with empty text (edge case).
        
        **Validates: Requirements 9.3, 9.4**
        """
        segment_id = f"{doc_hash}_{page}_0"
        original = DocumentSegment(
            id=segment_id,
            doc_hash=doc_hash,
            text="",
            page=page,
            bbox=BoundingBox(x=x, y=y, width=width, height=height)
        )
        
        # Serialize and deserialize
        json_str = json.dumps(asdict(original))
        deserialized_dict = json.loads(json_str)
        deserialized = DocumentSegment(
            id=deserialized_dict['id'],
            doc_hash=deserialized_dict['doc_hash'],
            text=deserialized_dict['text'],
            page=deserialized_dict['page'],
            bbox=BoundingBox(**deserialized_dict['bbox'])
        )
        
        # Verify empty text is preserved
        assert deserialized.text == "", "Empty text should be preserved"
        assert deserialized.id == original.id
        assert deserialized.doc_hash == original.doc_hash
        assert deserialized.page == original.page

    # Feature: wayfare-mvp-backend, Property 27: DocumentSegment序列化round-trip
    @given(
        doc_hash=valid_doc_hash(),
        page=st.integers(min_value=0, max_value=10000),
        x=valid_bbox_coordinate(),
        y=valid_bbox_coordinate(),
        width=valid_bbox_dimension(),
        height=valid_bbox_dimension()
    )
    @pytest.mark.property_test
    def test_unicode_text_round_trip(self, doc_hash, page, x, y, width, height):
        """Test round-trip with Unicode characters including emojis (edge case).
        
        **Validates: Requirements 9.3, 9.4**
        """
        # Test various Unicode scenarios
        unicode_texts = [
            "你好世界",  # Chinese
            "こんにちは",  # Japanese
            "안녕하세요",  # Korean
            "Hello 世界 🌍",  # Mixed with emoji
            "Math: ∑∫∂∇",  # Mathematical symbols
            "Arrows: ←→↑↓",  # Arrows
            "Special: \n\t\r",  # Whitespace characters
        ]
        
        for text in unicode_texts:
            segment_id = f"{doc_hash}_{page}_0"
            original = DocumentSegment(
                id=segment_id,
                doc_hash=doc_hash,
                text=text,
                page=page,
                bbox=BoundingBox(x=x, y=y, width=width, height=height)
            )
            
            # Serialize and deserialize
            json_str = json.dumps(asdict(original), ensure_ascii=False)
            deserialized_dict = json.loads(json_str)
            deserialized = DocumentSegment(
                id=deserialized_dict['id'],
                doc_hash=deserialized_dict['doc_hash'],
                text=deserialized_dict['text'],
                page=deserialized_dict['page'],
                bbox=BoundingBox(**deserialized_dict['bbox'])
            )
            
            # Verify Unicode text is preserved exactly
            assert deserialized.text == original.text, \
                f"Unicode text not preserved: {deserialized.text} != {original.text}"

    # Feature: wayfare-mvp-backend, Property 27: DocumentSegment序列化round-trip
    @given(
        doc_hash=valid_doc_hash(),
        page=st.integers(min_value=0, max_value=10000)
    )
    @pytest.mark.property_test
    def test_extreme_bbox_values_round_trip(self, doc_hash, page):
        """Test round-trip with extreme but valid bounding box values (edge case).
        
        **Validates: Requirements 9.3, 9.4**
        """
        # Test extreme values
        extreme_cases = [
            (0.0, 0.0, 0.1, 0.1),  # Minimum values
            (9999.9, 9999.9, 9999.9, 9999.9),  # Maximum values
            (0.0, 9999.9, 0.1, 9999.9),  # Mixed
            (123.456789, 987.654321, 555.555555, 777.777777),  # High precision
        ]
        
        for x, y, width, height in extreme_cases:
            segment_id = f"{doc_hash}_{page}_0"
            original = DocumentSegment(
                id=segment_id,
                doc_hash=doc_hash,
                text="test",
                page=page,
                bbox=BoundingBox(x=x, y=y, width=width, height=height)
            )
            
            # Serialize and deserialize
            json_str = json.dumps(asdict(original))
            deserialized_dict = json.loads(json_str)
            deserialized = DocumentSegment(
                id=deserialized_dict['id'],
                doc_hash=deserialized_dict['doc_hash'],
                text=deserialized_dict['text'],
                page=deserialized_dict['page'],
                bbox=BoundingBox(**deserialized_dict['bbox'])
            )
            
            # Verify extreme bbox values are preserved
            assert deserialized.bbox.x == original.bbox.x
            assert deserialized.bbox.y == original.bbox.y
            assert deserialized.bbox.width == original.bbox.width
            assert deserialized.bbox.height == original.bbox.height

    # Feature: wayfare-mvp-backend, Property 27: DocumentSegment序列化round-trip
    @given(
        doc_hash=valid_doc_hash(),
        page=st.integers(min_value=0, max_value=10000),
        x=valid_bbox_coordinate(),
        y=valid_bbox_coordinate(),
        width=valid_bbox_dimension(),
        height=valid_bbox_dimension()
    )
    @pytest.mark.property_test
    def test_very_long_text_round_trip(self, doc_hash, page, x, y, width, height):
        """Test round-trip with very long text (edge case).
        
        **Validates: Requirements 9.3, 9.4**
        """
        # Generate very long text (500 characters - maximum for segments)
        long_text = "A" * 500
        
        segment_id = f"{doc_hash}_{page}_0"
        original = DocumentSegment(
            id=segment_id,
            doc_hash=doc_hash,
            text=long_text,
            page=page,
            bbox=BoundingBox(x=x, y=y, width=width, height=height)
        )
        
        # Serialize and deserialize
        json_str = json.dumps(asdict(original))
        deserialized_dict = json.loads(json_str)
        deserialized = DocumentSegment(
            id=deserialized_dict['id'],
            doc_hash=deserialized_dict['doc_hash'],
            text=deserialized_dict['text'],
            page=deserialized_dict['page'],
            bbox=BoundingBox(**deserialized_dict['bbox'])
        )
        
        # Verify long text is preserved
        assert len(deserialized.text) == 500, "Long text length not preserved"
        assert deserialized.text == original.text, "Long text content not preserved"

    # Feature: wayfare-mvp-backend, Property 27: DocumentSegment序列化round-trip
    @given(
        doc_hash=valid_doc_hash(),
        page=st.integers(min_value=0, max_value=10000),
        x=valid_bbox_coordinate(),
        y=valid_bbox_coordinate(),
        width=valid_bbox_dimension(),
        height=valid_bbox_dimension()
    )
    @pytest.mark.property_test
    def test_special_characters_in_text_round_trip(self, doc_hash, page, x, y, width, height):
        """Test round-trip with special characters that might break JSON (edge case).
        
        **Validates: Requirements 9.3, 9.4**
        """
        # Test special characters that need escaping in JSON
        special_texts = [
            'Text with "quotes"',
            "Text with 'single quotes'",
            "Text with \\ backslash",
            "Text with / forward slash",
            "Text with \n newline",
            "Text with \t tab",
            "Text with \r carriage return",
            'Mixed: "quotes" \\ / \n \t',
        ]
        
        for text in special_texts:
            segment_id = f"{doc_hash}_{page}_0"
            original = DocumentSegment(
                id=segment_id,
                doc_hash=doc_hash,
                text=text,
                page=page,
                bbox=BoundingBox(x=x, y=y, width=width, height=height)
            )
            
            # Serialize and deserialize
            json_str = json.dumps(asdict(original))
            deserialized_dict = json.loads(json_str)
            deserialized = DocumentSegment(
                id=deserialized_dict['id'],
                doc_hash=deserialized_dict['doc_hash'],
                text=deserialized_dict['text'],
                page=deserialized_dict['page'],
                bbox=BoundingBox(**deserialized_dict['bbox'])
            )
            
            # Verify special characters are preserved
            assert deserialized.text == original.text, \
                f"Special characters not preserved: {deserialized.text} != {original.text}"
