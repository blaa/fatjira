from fatjira import IncrementalSearch

DOCS_FIXTURE = [
    # Complicated document to test recursive flattening
    {  # doc 0
        "field": "value",
        "subdict": {
            "a": "This is a text",
            "b": 1234,
            "c": 12.5,
        },
        "list": [
            "This is another piece of text", 50,
            ["rabbit hole", "goes deep"]
        ]
    },
    # wool/beer/cute search queries
    {  # doc 1
        "topic": "kittens are cute",
        "content": "wool and lasers",
    },
    {  # doc 2
        "topic": "bears are cute",
        "content": "wool and beer",
    }
]


class TestIncrementalSearch:

    def test_document_extraction(self):
        doc = DOCS_FIXTURE[0]
        extract = IncrementalSearch.recursive_extract_fn(doc)
        assert doc["field"] in extract
        assert "field" not in extract, "keys are not included"
        assert str(doc["subdict"]["b"]) in extract

    def test_query_normalization(self):
        inc = IncrementalSearch(DOCS_FIXTURE,
                                IncrementalSearch.recursive_extract_fn)
        inc.query = "this is query"
        assert inc.query == inc.get_normalized_query()

        inc.query = "this th thi this"
        assert inc.get_normalized_query() == "this"

        inc.query = "that is is"
        assert inc.get_normalized_query() == "that is"

        inc.query = "that is isthat"
        assert inc.get_normalized_query() == "that is isthat"

    def test_incremental_search(self):
        "Test incremental search mechanism"
        inc = IncrementalSearch(DOCS_FIXTURE,
                                IncrementalSearch.recursive_extract_fn)
        # Initially all documents are included in results
        results = inc.get_results()
        assert len(results) == len(DOCS_FIXTURE)

        # Search for a word matching only one document
        inc.search("wool")
        results = inc.get_results()
        assert len(results) == 2
        assert results[0] == DOCS_FIXTURE[1]
        assert results[1] == DOCS_FIXTURE[2]

        # Results are cached
        assert "wool" in inc.cache

        # Search forward
        inc.search("wool a")
        assert len(inc.current_results) == 2
        assert "wool a" in inc.cache
        assert "wool" in inc.cache

        inc.search("wool and")
        assert len(inc.current_results) == 2
        assert "wool a" in inc.cache
        assert "wool and" in inc.cache
        assert "wool" in inc.cache

        inc.search("wool and beer")
        assert len(inc.current_results) == 1
        assert inc.current_results[0] == 2
        assert "wool and" in inc.cache
        assert "wool and beer" in inc.cache

        # Search backward
        inc.search("wool and bee")
        assert len(inc.current_results) == 1
        assert inc.current_results[0] == 2
        assert "wool and" in inc.cache
        assert "wool and bee" in inc.cache
        assert "wool and beer" not in inc.cache

        # Empty search
        inc.search("wool and beetroot")
        assert len(inc.current_results) == 0
        assert "wool and bee" in inc.cache
        assert "wool and beetroot" in inc.cache
