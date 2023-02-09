### GPT3 Setup ###
import openai

openai.api_key = "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"
model_engine = "text-davinci-003"

def gpt3(prompt):
    # Generate a response
    completion = openai.Completion.create(
        engine=model_engine,
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.7,
    )

    response = completion.choices[0].text

    return response

### Prompt Engineering Task ###
# The target task is to evaluate small 3SAT truth assignments. To do this, I explain the general goal and give some examples of varying scale.
# I use Chain-of-Thought prompting to make the process more explicit, which in turn requires fewer shots to teach the task.

SAT_prompt = "In this task, we have some number of variables labeled x_1, x_2, through x_n and a given assignment of TRUE/FALSE values to those variables. Your task is to determine the value of the given Boolean expression under the given variable assignment. Here are a few step-by-step examples.\n" \
             "Expression = (x_1 OR x_2 OR -x_3) AND (-x_1 OR x_2 OR x_3), Assignment = (x_1=>TRUE, x_2=>FALSE, x_3=>TRUE)\n" \
             "Evaluation:\n" \
             "- Clause 1: x_1 evaluates to TRUE, x_2 evaluates to FALSE, -x_3 evaluates to FALSE. (x_1 OR x_2) => (TRUE OR FALSE) evaluates to TRUE. ((x_1 OR x_2) OR -x_3) => (TRUE OR FALSE) evaluates to TRUE. Clause 1 evaluates to TRUE.\n" \
             "- Clause 2: -x_1 evaluates to FALSE, x_2 evaluates to FALSE, x_3 evaluates to TRUE. (-x_1 OR x_2) => (FALSE OR FALSE) evaluates to FALSE. ((-x_1 OR x_2) OR x_3) => (FALSE OR TRUE) evaluates to TRUE. Clause 2 evaluates to TRUE.\n" \
             "- Total: Clause 1 AND Clause 2 => TRUE AND TRUE evaluates to TRUE.\n" \
             "Therefore, the expression evaluates to TRUE.\n" \
             "Expression = (-x_1 OR x_2 OR -x_3) AND (x_1 OR -x_2 OR x_3) AND (x_1 OR x_2 OR x_3), Assignment = (x_1=>FALSE, x_2=>TRUE, x_3=>FALSE)\n" \
             "Evaluation:\n" \
             "- Clause 1: -x_1 evaluates to TRUE, x_2 evaluates to FALSE, -x_3 evaluates to TRUE. (-x_1 OR x_2) => (TRUE OR FALSE) evaluates to TRUE. ((-x_1 OR x_2) OR -x_3) => (TRUE OR TRUE) evaluates to TRUE. Clause 1 evaluates to TRUE.\n" \
             "- Clause 2: x_1 evaluates to FALSE, -x_2 evaluates to FALSE, x_3 evaluates to FALSE. (-x_1 OR x_2) => (FALSE OR FALSE) evaluates to FALSE. ((-x_1 OR x_2) OR x_3) => (FALSE OR FALSE) evaluates to FALSE. Clause 2 evaluates to FALSE.\n" \
             "- Clause 3: x_1 evaluates to FALSE, x_2 evaluates to TRUE, x_3 evaluates to FALSE. (x_1 OR x_2) => (TRUE OR FALSE) evaluates to TRUE. ((x_1 OR x_2) OR x_3) => (TRUE OR TRUE) evaluates to TRUE. Clause 3 evaluates to TRUE.\n"\
             "- Total: Clause 1 AND Clause 2 AND Clause 3 => FALSE AND FALSE AND FALSE evaluates to FALSE.\n" \
             "Therefore, the expression evaluates to FALSE.\n" \

# For testing purposes
# expr is list of triplets of tuples (n, x) where n is a Boolean (n is True if the term is negated) and x is a variable index
# assign is a list of Booleans where x_i=>assign[i]
def gpt_3SAT_eval(expr, assign):
    expr_str = expr_to_str(expr)
    assign_str = assign_to_str(assign)

    response = gpt3(SAT_prompt + "Expression = %s, Assignment = %s\n" % (expr_str, assign_str))
    last = response.split(" ")[-1]

    if  last == "TRUE.":
        return True, response
    elif last == "FALSE.":
        return False, response
    else:
        raise Exception("GPT's response did not end in TRUE or FALSE. Here is what it output instead. \n" + response)

def expr_to_str(expr):
    expr_str = ""
    for clause in expr:
        expr_str += "("
        for var in clause:
            expr_str += ("-" if var[0] else "") + "x_" + str(var[1])
            expr_str += " OR " if var != clause[-1] else ""
        expr_str += ") AND " if clause != expr[-1] else ")"
    return expr_str
def assign_to_str(assign):
    return "(" + \
            str(["x_%d=>%s" % (i + 1, str(assign[i]).upper()) for i in range(len(assign))]).replace("[", "").replace(
                "]", "").replace("'", "") + \
            ")"

def gpt_3SAT_test(expr, assign):
    gpt_ans = gpt_3SAT_eval(expr, assign)
    real_ans = all([evaluate(clause, assign) for clause in expr])


    expr_str, assign_str = expr_to_str(expr), assign_to_str(assign)

    if gpt_ans[0] == real_ans:
        print("GPT3 correctly evaluated expression %s under assignment %s as %s." % (expr_str, assign_str, str(gpt_ans[0]).upper()))
        return
    else:
        raise Exception("GPT3 INCORRECTLY evaluated expression %s under assignment %s as %s. Here was its reasoning.\n%s" % (expr_str, assign_str, str(gpt_ans[0]).upper(), gpt_ans[1]))

def evaluate(clause, assign):
    t1, t2, t3 = clause
    return (t1[0] != assign[t1[1]-1]) or (t2[0] != assign[t2[1]-1]) or (t3[0] != assign[t3[1]-1])


expressions = [
    [((False, 1), (False, 2), (False, 3)),], # (x_1 OR x_2 OR x_3)
    [((False, 1), (False, 2), (False, 3)), ((True, 1), (True, 2), (True, 3))], # (x_1 OR x_2 OR x_3) AND (-x_1 OR -x_2 OR -x_3)
    [((False, 1), (True, 2), (False, 3)), ((True, 1), (False, 2), (True, 3))], # (x_1 OR -x_2 OR x_3) AND (-x_1 OR x_2 OR -x_3)
    [((False, 1), (False, 2), (False, 3)), ((True, 1), (False, 2), (False, 4)), ((True, 2), (False, 3), (True, 4))] # (x_1 OR x_2 OR x_3) AND (-x_1 OR x_2 OR x_4) AND (-x_2 OR x_3 OR -x_4)
               ]

for i in [True, False]: # 3 variables
    for j in [True, False]:
        for k in [True, False]:
            gpt_3SAT_test(expressions[-1], [i, j, k]) # Tests program on (x_1 OR x_2 OR x_3) for all truth assignments

"""for i in [True, False]: # 4 variables
    for j in [True, False]:
        for k in [True, False]:
            for l in [True, False]:
                gpt_3SAT_test(expressions[-1], [i, j, k, l]) # Tests program on (x_1 OR x_2 OR x_3) AND (-x_1 OR x_2 OR x_4) AND (-x_2 OR x_3 OR -x_4) for all truth assignments"""