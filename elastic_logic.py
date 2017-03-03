# Schema
import json

{
  "type": "object",
  "properties": {
    "operator" :{
      "type": "array"
    }
  }
}


# Example rules and data
# rules = {"and": [
#     {"<": [{"var": "temp"}, 110]},
#     {"==": [{"var": "pie.filling"}, "apple"]}
# ]}
#
# data = {"temp": 100, "pie": {"filling": "apple"}}

# print(jsonLogic(rules, data))
# True

def es2jsonlogic(rules, condition, operator):
        print("Condition: %s", condition)

        rule_key = next(iter(condition))

        if rule_key == "match":
            rule_value = condition[rule_key]
            for k,v in rule_value.items():
                 # subrule = {"==":[{"var":k},v]}
                 subrule = {"text_contains":[{"var":k},v]}
                 rules[operator].append(subrule)
        elif rule_key == "multi_match":
            for k in condition:
                fields = condition[k]["fields"]
                query_terms = condition[k]["query"].split(" ")

                subrule = {"or":[]}

                # subrule here is a compound OR of all the fields
                for field in fields:
                    for query in query_terms:
                        #subsubrule = {"==":[{"var":field},query]}
                        subsubrule = {"text_contains": [{"var": field}, query]}
                        subrule["or"].append(subsubrule)

                rules[operator].append(subrule)
        elif rule_key == "range":
            rule_value = condition[rule_key]
            for k,v in rule_value.items():
                # Now find the operator
                for i,j in v.items():
                    if i in ['gt','gte','lt','lte']:
                        range_operator = i.replace("gte",">=").replace("lte","<=").replace("gt",">").replace("lt","<")
                        value = j
                        subrule = {range_operator: [{"var": k}, value]}
                        rules[operator].append(subrule)
        elif rule_key == "exists":
            rule_value = condition[rule_key]

            for k,v in rule_value.items():
                subrule = {"exists":[{"var":v},None]}
                rules[operator].append(subrule)
        elif rule_key == "terms":
            rule_value = condition[rule_key]

            for k,v in rule_value.items():
                field = k
                values_array = v
                subrule = {"in":[{"var":field},values_array]}
                rules[operator].append(subrule)

        elif rule_key == "bool":
            # Recursively process this rule as if it were a top level condition and append result to parent condition
            bool_operator = next(iter(condition["bool"]))
            if bool_operator == "must":
                rec_operator = "and"
            elif bool_operator == "should":
                rec_operator = "or"
            elif bool_operator == "must_not":
                rec_operator = "and_not"
            else:
                raise ValueError("Elasticsearch boolean operator not supported")

            rec_rules = {
                           rec_operator:[]
                        }
            for rec_top_condition in condition["bool"][bool_operator]:
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
        elif bool_operator == "and_not":
            must_not_array = []
            for and_not_condition in rule_content:
                must_not_array = jsonlogic2es(must_not_array, and_not_condition)

                reverse_query.append({
                    "bool": {
                        "must_not": must_not_array
                    }
                })
        elif bool_operator in ['>','>=','<','<=']:
            field = rule_content[0]['var']
            variable = rule_content[1]
            range_operator = bool_operator.replace(">=", "gte").replace("<=", "lte").replace(">", "gt").replace("<", "lt")
            reverse_query.append({"range": {field: {range_operator:variable}}})
        elif bool_operator == "text_contains": # bool_operator == "==" or
            field = rule_content[0]['var']
            variable = rule_content[1]
            reverse_query.append({"match": {field:variable} })
        elif bool_operator == "exists":
            variable = rule_content[0]['var']
            reverse_query.append({"exists": {"field":variable}})
        elif bool_operator == "in":
            field = rule_content[0]['var']
            values_array = rule_content[1]
            reverse_query.append({"terms": {field:values_array}})
        elif bool_operator == "not_in":
            field = rule_content[0]['var']
            values_array = rule_content[1]

            must_not_query = {"bool":{"must_not":[{"terms": {field:values_array}   }]}}
            reverse_query.append(must_not_query)

        return reverse_query


def create_logic_object(es_query):
    logic = {
        "and": []
    }

    # 1. convert ES query to json rule
    for top_condition in es_query["query"]["bool"]["must"]:
        logic = es2jsonlogic(logic, top_condition, "and")

    print(json.dumps(logic, indent=4))

    print("-" * 20)

    # 2. convert json rule to es query
    final_reverse_query = {
        "query": {
            "bool": {
                "must": []
            }
        }
    }

    reverse_query = []
    for condition in logic["and"]:
        print("Condition: %s", condition)
        reverse_query = jsonlogic2es(reverse_query, condition)

    final_reverse_query["query"]["bool"]["must"] = reverse_query

    print("\nReverse Query:\n")
    print(json.dumps(final_reverse_query, indent=4))

    return logic

def create_es_query(logic):

    # 1. convert json rule to es query
    final_reverse_query = {
        "query": {
            "bool": {
                "must": []
            }
        }
    }

    reverse_query = []
    for condition in logic["and"]:
        print("Condition: %s", condition)
        reverse_query = jsonlogic2es(reverse_query, condition)

    final_reverse_query["query"]["bool"]["must"] = reverse_query

    print("\nReverse Query:\n")
    print(json.dumps(final_reverse_query, indent=4))

    print("-" * 20)

    logic = {
        "and": []
    }

    # 2. convert ES query to json rule
    for top_condition in final_reverse_query["query"]["bool"]["must"]:
        logic = es2jsonlogic(logic, top_condition, "and")

    print(json.dumps(logic, indent=4))


    return reverse_query
