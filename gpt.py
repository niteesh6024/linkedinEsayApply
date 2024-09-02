import warnings
import json
import demjson3
from datetime import datetime, timedelta
import google.generativeai as genai
warnings.filterwarnings('ignore')
import config
import time
import sys

request_times = []
with open(f'resume.txt', 'r') as file:
    resume = file.read()

def message(t):
    print("MSG: "+t)

def read_tries():
    with open(f'./data/tries.txt', 'r') as file:
        t = file.read().strip()
        current_date = datetime.now().strftime("%Y-%m-%d")
        file_date, tries_str = t.split(" tries=")
        tries = int(tries_str)
        if file_date != current_date:
            tries = 0
            write_tries(tries)
    return tries

def write_tries(tries):
    with open(f'./data/tries.txt', 'w') as file:
        current_date = datetime.now().strftime("%Y-%m-%d")
        file.write(f'{current_date} tries={tries}')



def ask_gpt_gemini(prompt):
    genai.configure(api_key=config.gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    result = model.generate_content(prompt,generation_config=genai.types.GenerationConfig(
        max_output_tokens=2048,
        temperature=0.3)).text
    return result

def ask_gpt(prompt):
    global request_times
    max_retries = 3
    tries = read_tries()
    if tries < 1500:
        now = datetime.now()
        request_times = [t for t in request_times if now - t < timedelta(seconds=60)]
    
        if len(request_times) >= 15:
            wait_time = 60 - (now - request_times[0]).total_seconds()
            message(f"Max request limit reached for this minute. wait for {wait_time} sec")
            time.sleep(wait_time+1)
            
        for attempt in range(max_retries):
            try:
                result = ask_gpt_gemini(prompt)
                tries += 1
                request_times.append(datetime.now())
                write_tries(tries)
                return result
            except Exception as e:
                message(f"Error in Gemini on attempt {attempt + 1}: {e}")
    else:
        message("Max tries limit reached for the day.")
        sys.exit(0)
    return None

def get_keys_from_gpt_response(final_answer):
    import re
    json_str = re.search(r'```json(.+?)```', final_answer, re.DOTALL)
    if json_str:
        cleaned_str = json_str.group(1).strip()
    else:
        final_answer = final_answer.replace('\n', '')
        #final_answer = final_answer.replace(' ', '')
        final_answer = re.sub(r'\s(?=(?:[^\'"]*[\'"][^\'"]*[\'"])*[^\'"]*$)', '', final_answer)
        final_answer = re.sub(r'^.*?({)', r'\1', final_answer)
        final_answer = re.sub(r'(}).*$', r'\1', final_answer) 
        final_answer = final_answer.replace('True', 'true').replace('False', 'false')                       
        cleaned_str = final_answer
    try:
        
        data_dict = demjson3.decode(cleaned_str)
        #data_dict = json.loads(cleaned_str)
        if isinstance(data_dict, list):
            final_box_answers = [list(item.values()) for item in data_dict]
            final_box_answers = [item for sublist in final_box_answers for item in sublist]
        else:
            final_box_answers = list(data_dict.values())
            try:
                final=[]
                for f in final_box_answers:
                    final.append(f.split(":")[-1])
                final_box_answers=final
            except:
                pass
        return final_box_answers
    except json.JSONDecodeError:
        print("Could not decode JSON")
        return []
    
def make_prompt(questions_set):
        prompt = ""
        prompt =f"""I have attached my resume below: ```"{resume}" 
        ```. Read the above resume carefully and understand the information in it. You are applying for the job by answering the below questions behalf of the candidate in Linkedin website.
        
        Now, answer the following questions step by step:
        """
        count =0
        for question in questions_set:
            count +=1
            prompt += f"Question {count}: {question}: \n"
        prompt = prompt + """Begin by extracting pertinent information from the resume. Approach each question methodically, answering them one at a time using the information provided in the resume. If a question isn't directly answered in the resume, use creative thinking to provide an approximate answer based on the available information. Ensure to answer all questions in the order they are presented. Remember to first strategize each answer step by step before providing the final response. If the answer to the question is not given in the resume, Then you should estimate it creatively from the given information without saying that you don't know or not specified. 
        Always remember to approximate answer creatively even if the answer is not mentioned in the resume.
        Always remember that you should not say Not specified or provided in the given information, You have to estimate the answer creatively from the given information.
        Answer it in good markdown format. with each question as side heading and it's explanation of answer below it. Also answer in the asked format (whole number as integer or float or string).                        
        """
        return prompt 
def make_prompt2(questions_set , answer):
        prompt =f"""
        You are applying for the job by answering the below questions behalf of the candidate in Linkedin website. 
        Take the information from the following ```{answer}``` and answer the below questions.
        Here are the questions:
        """
        count =0
        for question in questions_set:
            count +=1
            prompt += f"Question {count}: {question}: \n"
        prompt = prompt + f""" Provide answers to the questions exclusively, formatted in valid Python Dictionary, with the question index as the key and the corresponding answer as the value. Exclude any explanations, extraneous details, or elements beyond the direct answer. Ensure the response conforms to the specified format, such as integer or whole number. When making assumptions for the answer, highlight positive and advantageous characteristics, taking into account the individual's comprehensive expertise and experience. Present the answer in Dictionary format, devoid of any additional explanations. Note that you are answering the question where you have to fill the answers in the box, So tell the exact answer. Read the question carefully and answer in required format (whole number as integer or float or string).If the answer to the question is not given in the information
        , Then you should estimate it creatively from the given information without saying that you don't know or not specified. 
        Remember to follow the correct dictionary format for the answer with the key as question number and value as the answer and don't use dictionary in the value. You should not use nested dictionary structure, you should only give key as the question number and value as the exact answer to the question in string.  If it was mentioned in the question to follow specific format like whole number or float number, then follow that carefully. 

        """
        return prompt

def remove_duplicates(input_list):
    result = []

    for item in input_list:
        if item not in result:
            result.append(item)
    
    return result
def make_prompt_radio(questions_set):
    prompt = ""
    prompt =f"""I have attached my resume below: ```"{resume}" 
    ```
    
    Now, answer the following questions step by step by marking the appropriate radio button:
    """
    count =0
    for question in questions_set:
        count +=1
        prompt += f"Question {count}: {question}: \n"
    prompt = prompt + """Start by pulling out relevant information from the resume and approach each question systematically. Use the information from the resume to answer each question in sequence. If a question isn't directly addressed in the resume, use your creativity to provide a reasonable answer based on the available information. Ensure to answer all questions in the order they're given. Remember to strategize each answer step by step before providing the final response.Don't say that you don't know the answer or Not mentioned, estimate the answer according to the resume creatively. You have to only select the answer from the radio buttons and don't say that you don't know or not specified. If the answer is not present in the resume, then estimate it creatively and don't say it is not mentioned or not specified.

    
    """
    return prompt 
def make_prompt2_radio(questions_set , answer):
    prompt =f"""
    Take the information from the following ```{answer}``` and answer the below questions.
    Here are the questions:
    """
    count =0
    for question in questions_set:
        count +=1
        prompt += f"Question {count}: {question}: \n"
    prompt = prompt + f"""Provide only the answers to the questions, formatted in valid Python Dictionary. Use the question index as the key and the corresponding answer as the value. Avoid including explanations, unnecessary details, or any elements beyond the direct answer. Ensure your response conforms to the specified format, such as integer or whole number. Present the answer in Dictionary format, without any additional explanations. Note that you are responding to a question with radio button options, so provide only the answer without additional explanations. If the answer is not specified, you can take assumptions on the answer based on the given information and you should not say that you don't know or not specified.  """
    return prompt
