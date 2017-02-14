from json_logic import jsonLogic
import json


# Schema
{
  "type": "object",
  "properties": {
    "operator" :{
      "type": "array"
    }
  }
}

def es2jsonlogic(rules,top_condition,operator):
        print("Top condition %s",top_condition)

        rule_key = next(iter(top_condition))

        if rule_key == "match":
            rule_value = top_condition[rule_key]
            for k,v in rule_value.items():
                 subrule = {"==":[{"var":k},v]}
                 rules[operator].append(subrule)
        elif rule_key == "multi_match":
            for k in top_condition:
                fields = top_condition[k]["fields"]
                query = top_condition[k]["query"]

                subrule = {"or":[]}

                # subrule here is a compound OR of all the fields
                for field in fields:
                    subsubrule = {"==":[{"var":field},query]}
                    subrule["or"].append(subsubrule)

                rules[operator].append(subrule)
        elif rule_key == "range":
            rule_value = top_condition[rule_key]
            for k,v in rule_value.items():
                # Now find the operator
                for i,j in v.items():
                    if i in ['gt','gte','lt','lte']:
                        range_operator = i.replace("gte",">=").replace("lte","<=").replace("gt",">").replace("lt","<")
                        value = j
                        subrule = {range_operator: [{"var": k}, value]}
                        rules[operator].append(subrule)

        elif rule_key == "bool":
            # Recursively process this rule as if it were a top level condition and append result to parent condition
            bool_operator = next(iter(top_condition["bool"]))
            if bool_operator == "must":
                rec_operator = "and"
            elif bool_operator == "should":
                rec_operator = "or"
            else:
                raise ValueError("Elasticsearch boolean operator no supported")

            rec_rules = {
                           rec_operator:[]
                        }
            for rec_top_condition in top_condition["bool"][bool_operator]:
                rec_rules = es2jsonlogic(rec_rules,rec_top_condition,rec_operator)

            # Append the result of the recursion to the original
            rules[operator].append(rec_rules)

        return rules

def jsonlogic2es(reverse_query, condition):
        bool_operator = next(iter(condition))
        rule_content = condition[bool_operator]

        if bool_operator == "and":
            must_array = []
            for and_condition in rule_content:
                must_array = jsonlogic2es(must_array, and_condition)
            reverse_query.append({
                "bool": {
                    "must": must_array
                }
            })
        elif bool_operator == "or":
            # This is going to be an array of rules
            should_array = []
            for or_condition in rule_content:
                should_array = jsonlogic2es(should_array, or_condition)
            reverse_query.append({
                "bool": {
                    "should": should_array
                }
            })
        elif bool_operator in ['>','>=','<','<=']:
            field = rule_content[0]['var']
            variable = rule_content[1]
            range_operator = bool_operator.replace(">=", "gte").replace("<=", "lte").replace(">", "gt").replace("<", "lt")
            reverse_query.append({"range": {field: {range_operator:variable}}})
        elif bool_operator == "==":
            field = rule_content[0]['var']
            variable = rule_content[1]
            reverse_query.append({"match": {field:variable} })

        return reverse_query



if __name__ == '__main__':
    es_query = {
        "query" : {
            "bool" : {
                "must" : [
                    {"match": {"title": "Search"}},
                    {
                        "multi_match" : {
                            "fields" : ["md5", "title", "resource_name", "processing_title", "text_addition", "extracted_text"],
                            "query" : "domain"
                        }
                    }, {
                        "bool" : {
                            "must" : [{
                                    "match" : {
                                        "classification.term" : "Contract"
                                    }
                                }, {
                                    "range" : {
                                        "classification.proba" : {
                                            "gte" : 0.8,
                                            "boost" : 2
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


    #Example rules and data
    rules = {"and": [
        {"<": [{"var": "temp"}, 110]},
        {"==": [{"var": "pie.filling"}, "apple"]}
    ]}

    data = {"temp": 100, "pie": {"filling": "apple"}}

    # print(jsonLogic(rules, data))
    # True

    rules = {
       "and":[]
    }

    # 1. convert ES query to json rule
    for top_condition in es_query["query"]["bool"]["must"]:
        rules = es2jsonlogic(rules,top_condition,"and")

    print(json.dumps(rules, indent=2))

    print("-"*20)


    # 2. convert json rule to es query
    final_reverse_query = {
        "query": {
            "bool": {
                "must":[]
            }
        }
    }

    reverse_query = []
    for condition in rules["and"]:
        print(condition)
        reverse_query = jsonlogic2es(reverse_query,condition)

    final_reverse_query["query"]["bool"]["must"].append(reverse_query)
    print(final_reverse_query)
    
    
    # 3. Assertion with new data
    data = {"title":"Search"}
    print(jsonLogic(rules, data))
    #False

    data = {"title": "Search","md5":"domain"}
    print(jsonLogic(rules, data))
    #False

    data = {"title": "Search", "md5": "domain","classification":{"term":"Contract","proba":0.8}}
    print(jsonLogic(rules, data))
    #True