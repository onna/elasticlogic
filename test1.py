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

    logic = create_logic_object(es_query=es_query)

    # 3. Assertion with new data
    #{"==":[{"var":"title"},"Search"]}
    data = {"title": "treASure"}
    assert jsonLogic(logic, data)

    data = {"extracted_text": "I found a nice treasure."}
    assert not jsonLogic(logic,data)

    data = {"title": "something else"}
    assert not jsonLogic(logic, data)

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
                            "query": "treasure chest"
                        }
                    }
                ]
            }
        }
    }

    logic = create_logic_object(es_query=es_query)

    data = {"title": "treasure"}
    assert jsonLogic(logic, data)

    data = {"title": "I found a Treasure on the island"}
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

def test_exists():
    #{'exists': [{'var': 'field'}, 'processing_date']}
    es_query = {
        "query": {
            "bool": {
                "must": [{
                    "exists": {
                        "field": "processing_date"
                    }
                }]
            }
        }
    }


    logic = create_logic_object(es_query=es_query)

    # Condition met
    data = {"processing_date": "11-11-2016"}
    assert jsonLogic(logic, data)

    data = {"someotherdate": "11-11-2016"}
    assert not jsonLogic(logic, data)

    data = {"processing_date": None}
    assert not jsonLogic(logic, data)

def test_terms():
    es_query = {
        "query": {
            "bool": {
                "must": [{
                    "terms": {
                        "extension": ["jpeg","pdf"]
                    }
                }
                ]
            }
        }
    }

    logic = create_logic_object(es_query=es_query)

    # Condition met
    data = {"extension": "pdf"}
    assert jsonLogic(logic, data)

    data = {"extension": "pdfx"}
    assert not jsonLogic(logic, data)

    data = {"extension": "JPEG"}
    assert jsonLogic(logic, data)

# def test_phrase():
#     es_query = {
#         "query": {
#             "bool": {
#                 "must": [{
#                     "multi_match": {
#                         "query": "this is a phrase",
#                         "type": "phrase",
#                         "fields": ["title", "resource_name", "processing_title", "text_addition", "extracted_text"]
#                     }
#                 }
#                 ]
#             }
#         }
#     }
#     logic = create_logic_object(es_query=es_query)
#
#     # Condition met
#     data = {"extracted_text": "this is a phrase"}
#     assert jsonLogic(logic, data)
#
#     data = {"extracted_text": "this is a"}
#     assert not jsonLogic(logic, data)
#
#     data = {"extracted_text": "making sure this is a phrase that's found"}
#     assert jsonLogic(logic, data)

def test_simple_query():
    es_query = {
                "query": {
                    "bool": {
                        "must": [{
                                "exists": {
                                    "field": "processing_date"
                                }
                            },{
                                "multi_match": {
                                    "query": "term1 term3",
                                    "type": "cross_fields",
                                    "fields": ["md5_text", "title", "resource_name", "processing_title", "text_addition", "extracted_text"]
                                }
                            },{
                                "terms": {
                                    "parent_datasource.id": ["18d58f4c148b4fdd9c13efebc93b67cc"]
                                }
                            },{
                                "multi_match": {
                                    "query": "this is a phrase",
                                    "type": "phrase",
                                    "fields": ["title", "resource_name", "processing_title", "text_addition", "extracted_text"]
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
                                                    "gte": 0.85
                                                }
                                            }
                                        }
                                    ]
                                }
                            }, {
                                "terms": {
                                    "extension": ["jpeg"]
                                }
                            }
                        ]
                    }
                }
            }
    logic = create_logic_object(es_query=es_query)

    # 3. Assertion with new data


    data = {"title": "term1"}
    assert not jsonLogic(logic, data)

    data = {
        "processing_date": "11-11-2016",
        "extracted_text": "term1 term3",
        "title": "this is a phrase",
        "parent_datasource": {
            "id": "18d58f4c148b4fdd9c13efebc93b67cc"
        },
        "classification": {
            "term": "Contract",
            "proba": 0.9
        },
        "extension": "JPEG"
    }

    assert jsonLogic(logic, data)


def test_starting_onna_query():
    es_query = {
                "query": {
                    "bool": {
                        "must": [
                                {
                                "bool": {
                                    "should": [{
                                            "bool": {
                                                "must": [{
                                                        "match": {
                                                            "classification.term": "Contract"
                                                        }
                                                    }, {
                                                        "range": {
                                                            "classification.proba": {
                                                                "gte": 0.85
                                                            }
                                                        }
                                                    }
                                                ]
                                            }
                                        }, {
                                            "terms": {
                                                "extension": ["jpeg", "pdf"]
                                            }
                                        }, {
                                            "range": {
                                                "modifiedDate": {
                                                    "gt": "2016-01-15"
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
    logic = create_logic_object(es_query=es_query)

    # 3. Assertion with new data


    data = {"title": "term1"}
    assert not jsonLogic(logic, data)

    data = {
        "modifiedDate": "2016-11-11",
        "title": "going to play sOCCer tonight",
        "extracted_text" : "tell me if this is a phrase? ",
        "classification": {
            "term": "Contract",
            "proba": 0.9
        },
        "extension": "JPEG"
    }

    assert jsonLogic(logic, data)


