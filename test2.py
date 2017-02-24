from json_logic import jsonLogic
from elastic_logic import create_logic_object

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

def test_phrase():
    es_query = {
        "query": {
            "bool": {
                "must": [{
                    "multi_match": {
                        "query": "this is a phrase",
                        "type": "phrase",
                        "fields": ["title", "resource_name", "processing_title", "text_addition", "extracted_text"]
                    }
                }
                ]
            }
        }
    }
    logic = create_logic_object(es_query=es_query)

    # Condition met
    data = {"extracted_text": "this is a phrase"}
    assert jsonLogic(logic, data)

    data = {"extracted_text": "this is a"}
    assert not jsonLogic(logic, data)

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

