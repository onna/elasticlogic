from json_logic import jsonLogic
from elastic_logic import create_logic_object

def test_match():
    es_query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"title": "treasure"}}
                ]
            }
        }
    }

    rules = create_logic_object(es_query=es_query)

    # 3. Assertion with new data
    #{"==":[{"var":"title"},"Search"]}
    data = {"title": "treASure"}
    assert jsonLogic(rules, data)

    data = {"title": "something else"}
    assert not jsonLogic(rules, data)

def test_number_match():
    es_query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"depth": 0}}
                ]
            }
        }
    }

    rules = create_logic_object(es_query=es_query)

    # 3. Assertion with new data
    #{"==":[{"var":"title"},"Search"]}
    data = {"depth": 0}
    assert jsonLogic(rules, data)

    data = {"depth": "something else"}
    assert not jsonLogic(rules, data)

    data = {"depth": 1}
    assert not jsonLogic(rules, data)

def test_multimatch():
    es_query = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "fields": ["md5", "title", "resource_name", "processing_title", "text_addition",
                                       "extracted_text"],
                            "query": "treasure"
                        }
                    }
                ]
            }
        }
    }

    logic = create_logic_object(es_query=es_query)

    data = {"title": "treasure"}
    assert jsonLogic(logic, data)

    data = {"title": "coal"}
    assert not jsonLogic(logic, data)
    
    data = {"completely":"unrelated"}    
    assert not jsonLogic(logic, data)

def test_combination_query():
    es_query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"title": "Search"}},
                    {
                        "multi_match": {
                            "fields": ["md5", "title", "resource_name", "processing_title", "text_addition",
                                       "extracted_text"],
                            "query": "domain"
                        }
                    }, {
                        "bool": {
                            "must": [{
                                "match": {
                                    "classification.term": "Contract"
                                }
                            }, {
                                "range": {
                                    "classification.proba": {
                                        "gte": 0.8,
                                        "boost": 2
                                    }
                                }
                            }
                            ]
                        }
                    }
                ]
            }
        }
    }

    rules = create_logic_object(es_query=es_query)

    # 3. Assertion with new data
    #{"==":[{"var":"title"},"Search"]}
    # Just title
    data = {"title": "Search"}
    assert not jsonLogic(rules, data)

    # Just title and md5
    data = {"title": "Search", "md5": "domain"}
    assert not jsonLogic(rules, data)

    # All conditions met
    data = {"title": "Search", "md5": "domain", "classification": {"term": "Contract", "proba": 0.8}}
    assert jsonLogic(rules, data)

