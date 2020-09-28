# TODO: Threading / Parallel without blocking the UI

class IncrementalSearch:
    """
    Universal incremental search within a list of documents.
    """

    def __init__(self, documents, extract_fn):
        self.query = ""
        self.documents = documents[:]
        # Extracted texts related to the documents by index
        self.extracts = []
        # { "query": [result_idx1, ...], "query a": [result_idx2, ...], ...}
        self.cache = {}
        self.current_results = list(range(len(documents)))
        for doc in self.documents:
            extract = extract_fn(doc)
            self.extracts.append(extract)

    def get_normalized_query(self):
        """
        Normalize whitespaces and remove duplicates while preserving order
        """
        input_terms = self.query.split()
        final_terms = []
        for term in input_terms:
            # Is the current term a prefix of other already present term?
            dups = [t for t in final_terms if t.startswith(term)]
            if dups:
                # Drop term.
                continue
            final_terms.append(term)
        return " ".join(final_terms)

    def get_results(self, max_results=2**32):
        return [
            self.documents[idx]
            for idx in self.current_results[:max_results]
        ]

    def _invalidate_cache(self, query):
        "Remove cached results not matching the current query"
        # Remove non-prefix cached results
        for cached_query in list(self.cache.keys()):
            if not query.startswith(cached_query):
                del self.cache[cached_query]
        # TODO: Maybe keep them if there's less than X entries? Or based on time.

    def _find_best_cache(self, query):
        "Find best cached results to build next search"
        # Find best matching base results
        for cut in range(len(query), 0, -1):
            part = query[:cut]
            if part in self.cache:
                return self.cache[part], part
        return list(range(len(self.documents))), ""

    def search(self, new_query):
        """
        Add/remove a character in query - usually at the end.
        """
        self.query = new_query
        query = self.get_normalized_query()

        self._invalidate_cache(query)
        cache, cached_query = self._find_best_cache(query)

        cached_terms = set(cached_query.split())
        query_terms = set(query.split())
        new_terms = query_terms - cached_terms

        if not new_terms:
            self.current_results = cache
            return

        # Prepare terms
        terms_sensitive = set()
        terms_insensitive = set()
        for term in new_terms:
            if term == term.lower():
                terms_insensitive.add(term)
            else:
                terms_sensitive.add(term)

        new_results = []
        for idx in cache:
            extract = self.extracts[idx]
            extract_lower = extract.lower()
            keep = True
            for term in terms_sensitive:
                if term not in extract:
                    keep = False
                    break
            if keep:
                for term in terms_insensitive:
                    if term not in extract_lower:
                        keep = False
                        break
            if keep:
                new_results.append(idx)

        # Remember result
        self.cache[query] = new_results
        self.current_results = new_results

    @staticmethod
    def recursive_extract_fn(document):
        "Extract data from dictionary resursively as string"
        parts = []
        if isinstance(document, dict):
            for key, subvalue in document.items():
                parts.append(IncrementalSearch.recursive_extract_fn(subvalue))
        elif isinstance(document, (list, set)):
            for element in document:
                parts.append(IncrementalSearch.recursive_extract_fn(element))
        elif isinstance(document, (int, float)):
            parts.append(str(document))
        elif isinstance(document, str):
            parts.append(document)
        elif document is None:
            return ""
        else:
            raise Exception(f"Type {type(document)} is unhandled")
        return " ".join(parts)
