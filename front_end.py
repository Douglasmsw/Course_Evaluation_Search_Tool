import bs4
import os
import course_evals as ce
import re
import pandas as pd
from skimage import io
import matplotlib.pyplot as plt
from tabulate import tabulate

#--------------------READING FILE IN FOR FRONT END
#REMINDER:
#Courses denoted with div tags of form <div class=course, id=course_code, style=indicate if there is feedback for course>
#Profs denoted with div tags of form <div class="prof" id="prof_name" title="course_code" tabindex="quarter">

def index_file_to_soup(file_name):
    if not isinstance(file_name, str):
        raise ValueError('File name input must be a string')
    index_file = open(file_name, 'r')
    index_data = index_file.read()
    soup = bs4.BeautifulSoup(index_data, 'lxml')
    return soup

def de_list_items(set):
    item_set = set()
    for item in set:
        if isinstance(item, list):
            item = ' '.join(item)
            item_set.add(item)
        else:
            item_set.add(item)
    return item_set

def course_set(soup):
    courses = soup.find_all('div', class_='course', style='feedback')
    courses = set(courses)
    classes_set = set()
    for course in courses:
        classes_set.add(course['id'])
    return classes_set
    
def build_references(file_name):
    soup = index_file_to_soup(file_name)
    classes_set = course_set(soup)
    return soup, classes_set;
    
#-----------------GENERATING COURSE SEARCH LIST VIA USER INTERACTION

def is_valid_course(classes_set, search):
    if search in classes_set:
        return True
    return False

def yes_or_no(input_str):
    affirmative = {'y', 'Y', 'yes', 'Yes', 'YES', 'yeah', 'Yeah', 'sure', 'Sure', 'yea', 'ye'}
    negative = {'n', 'N', 'NO', 'no', 'No', 'nah', 'Nah', 'nope', 'Nope'}
    response = input(input_str + ' (y/n)\n')
    if response in affirmative:
        return True
    if response in negative:
        return False
    print('Please re-enter your answer when prompted as either "y" or "n" for "yes" and "no" respectively.')
    return yes_or_no(input_str)

def list_to_unique(ls):
    ls_unique = []
    for item in ls:
        if item not in ls_unique:
            ls_unique.append(item)
    return ls_unique

def course_search_target(classes_set):
    course_code = input("Please input the course code of the class you'd like to search in the format: DEPT 12345 \n")
    course_code = course_code.upper()
    if not is_valid_course(classes_set, course_code):
        print('The course code you input was not valid or has no feedback.')
        add_another = yes_or_no('Would you like to continue adding classes to your search?')
        if add_another == True:
            return course_search_target(classes_set)
        search_target = []
        return search_target, add_another;
    search_target = [course_code]
    add_another = yes_or_no('Would you like to see / compare results to another class?')
    return search_target, add_another;

def make_search_list(classes_set):
    add_another = True
    search_list = []
    while add_another == True:
        search_item, add_another = course_search_target(classes_set)
        search_list += search_item
    search_list = list_to_unique(search_list)
    return search_list
    
def search_to_tags(soup, search_list):
    search_tags = []
    for search in search_list:
        tag = soup.find('div', class_='course', id=search)
        search_tags.append(tag)
    return search_tags

def start_search(file_name):
    print('Please give us a minute to load in the course feedback data')
    soup, classes_set = build_references(file_name)
    print('Ok, all booted up!')
    search_list = make_search_list(classes_set)
    search_tags = search_to_tags(soup, search_list)
    return search_tags
    
#----------------------PULLING RELEVANT COURSE OBJECTS BASED ON SEARCH LIST
#GOAL:
#Revert course tag html into course objects

#code has course code and profs is a dictionary of form: key = prof name, value = prof object

#Courses denoted with div tags of form <div class=course, id=course_code, style=indicate if there is feedback for course>

class Course:
    def __init__(self, code, profs):
        self.code = code
        self.profs = profs

#name is prof name, quarter is the quarter (season year), and the eval is an eval dictionary of form: key = question, value = response

#Profs denoted with div tags of form <div class="prof" id="prof_name" title="course_code" tabindex="quarter">

class Prof:
    def __init__(self, name, eval, quarter):
        self.name = name
        self.quarter = quarter
        self.eval = eval

def strip_div_label(tag):
    tag = str(tag)
    tag = re.sub('(<div.+?>)|(</div>)', '', tag)
    tag = bs4.BeautifulSoup(tag, "lxml")
    return tag

def prof_tag_to_eval_dict(prof_tag):
    questions_html = prof_tag.find_all('div', class_ = 'question')
    eval_dict = {}
    for question in questions_html:
        key = question['id']
        value = strip_div_label(question)
        eval_dict[key] = value
    return eval_dict
        
def unpack_prof_attrs(prof_tag):
    name = prof_tag['id']
    quarter = prof_tag['tabindex']
    return name, quarter;

def prof_tag_to_object(prof_tag):
    name, quarter = unpack_prof_attrs(prof_tag)
    eval = prof_tag_to_eval_dict(prof_tag)
    prof_object = Prof(name, eval, quarter)
    return prof_object

def build_prof_dict(prof_tag_list):
    prof_dict = {}
    for prof_tag in prof_tag_list:
        prof_object = prof_tag_to_object(prof_tag)
        prof_name = prof_object.name
        prof_dict[prof_name] = prof_object
    return prof_dict

#Courses denoted with div tags of form <div class=course, id=course_code, style=indicate if there is feedback for course>

def unpack_course_attrs(course_tag):
    code = course_tag['id']
    return code

def course_tag_to_object(course_tag):
    code = unpack_course_attrs(course_tag)
    prof_tag_list = course_tag.find_all('div', class_ = 'prof')
    profs = build_prof_dict(prof_tag_list)
    course_object = Course(code, profs)
    return course_object
    
def search_tags_to_course_objects(search_tags):
    search_objects = []
    for course_tag in search_tags:
        course_object = course_tag_to_object(course_tag)
        search_objects.append(course_object)
    return search_objects
    
#----------------------ASK WHICH PROFESSORS THEY'D LIKE TO COMPARE

def pull_prof_names(search_data):
    class_prof_dict = {}
    for course_object in search_data:
        course_code = course_object.code
        prof_name_list = list(course_object.profs.keys())
        class_prof_dict[course_code] = prof_name_list
    return class_prof_dict

def display_profs(course_code, prof_name_list):
    print(course_code + ':')
    end_index = len(prof_name_list)
    for i in range(end_index):
        prof_name = prof_name_list[i]
        print('\t' + str(i+1) + ') ' + prof_name)
    print('\t' + str(end_index+1) + ') ' + 'All professors')

def prof_list_index(prof_name_list):
    selection = input("Please type the number labels of the professors you'd like to see feedback for in the form: 1,2,3,4,5 etc. as a list separated by commas \n")
    selection = selection.split(',')
    try:
        selection_list = [int(num) - 1 for num in selection]
        return selection_list
    except:
        print('There was an issue with your number list input, please re-type when prompted.')
        return prof_list_index(prof_name_list)

def which_profs(class_prof_dict):
    chosen_profs_dict = {}
    for course_code in class_prof_dict:
        prof_name_list = class_prof_dict[course_code]
        display_profs(course_code, prof_name_list)
        selection_list = prof_list_index(prof_name_list)
        profs_list = []
        for index in selection_list:
            if index == len(prof_name_list):
                profs_list = prof_name_list
            else:
                selected_name = prof_name_list[index]
                profs_list.append(selected_name)
        chosen_profs_dict[course_code] = profs_list
    return chosen_profs_dict
    
#Now that we have a dictionary where keys = course codes and values = professor names that user wants to see evaluations of, it's time to 1) pull the relevant evaluation data and 2) generate the list of questions to select from.

#take in dictionary where keys = course codes and values = lists of professor names and the search_data which is a list of course objects. Then returns a dictionary where keys = course codes and values = dictionary [keys=professor names and values=professor objects]

def pull_chosen_prof_evals(chosen_profs_dict, search_data):
    chosen_prof_evals = {}
    for course_object in search_data:
        course_dict = {}
        course_code = course_object.code
        desired_profs = set(chosen_profs_dict[course_code])
        prof_object_dict = course_object.profs
        for prof in prof_object_dict:
            if prof in desired_profs:
                course_dict[prof] = prof_object_dict[prof]
        chosen_prof_evals[course_code] = course_dict
    return chosen_prof_evals

#----------------------USE CHOSE PROF OBJECTS TO GENERATE LIST OF UNQUE QUESTIONS

#take in chosen_prof_evals (keys = course codes and values = dictionary [keys=professor names and values=professor objects]) and return list of unique questions that appear in the professor evaluations.

def eval_dict_to_q_set(eval_dict):
    q_set = set()
    for question in eval_dict:
        q_set.add(question)
    return q_set
    
def prof_dict_to_q_set(prof_dict):
    q_set = set()
    for prof_name in prof_dict:
        prof_object = prof_dict[prof_name]
        eval_dict = prof_object.eval
        prof_q_set = eval_dict_to_q_set(eval_dict)
        q_set.update(prof_q_set)
    return q_set

def pull_unique_q_set(chosen_prof_evals):
    unique_q_set = set()
    for course_code in chosen_prof_evals:
        prof_dict = chosen_prof_evals[course_code]
        course_q_set = prof_dict_to_q_set(prof_dict)
        unique_q_set.update(course_q_set)
    return unique_q_set

def unique_question_list(chosen_prof_evals):
    unique_q_set = pull_unique_q_set(chosen_prof_evals)
    question_list = list(unique_q_set)
    return question_list
    
def search_data_to_q_list(search_data):
    class_prof_dict = pull_prof_names(search_data)
    chosen_profs_dict = which_profs(class_prof_dict)
    chosen_prof_evals = pull_chosen_prof_evals(chosen_profs_dict, search_data)
    print('\n')
    question_list = unique_question_list(chosen_prof_evals)
    return question_list, chosen_prof_evals;
    
#REMINDER: search_data is a list of course objects from the user search. The question_list is a list of strings, each being a unique question that appears among the professors and courses searched
    
#------------------------Display questions to user and have them select which they'd like to see the evaluations for.

#modify below code from the professor select functions to prompt user to select index of the questions they want to see. Note that not all professors may have a response to a chosen question.

def display_questions(question_list):
    print('Below are the questions that appear in the selected professor evaluations: \n')
    end_index = len(question_list)
    for i in range(end_index):
        question = question_list[i]
        print('\t' + str(i+1) + ') ' + question)
    print('\t' + str(end_index+1) + ') ' + 'All questions')

def question_list_index(question_list):
    selection = input("\nPlease type the number labels of the questions you'd like to see feedback for in the form: 1,2,3,4,5 etc. as a list separated by commas \n")
    selection = selection.split(',')
    try:
        selection_list = [int(num) - 1 for num in selection]
        return selection_list
    except:
        print('There was an issue with your number list input, please re-type when prompted.')
        return question_list_index(question_list)
        
def which_questions(question_list):
    display_questions(question_list)
    selection_index = question_list_index(question_list)
    chosen_questions = []
    for index in selection_index:
        if index == len(question_list):
            profs_list = prof_name_list
        else:
            selected_question = question_list[index]
            chosen_questions.append(selected_question)
    return chosen_questions

#-------------------------function to go to do entire search to questions, input should be soup and classes_set from build_references function:
    
def select_classes_profs_questions(soup, classes_set):
    search_list = make_search_list(classes_set)
    search_tags = search_to_tags(soup, search_list)
    search_data = search_tags_to_course_objects(search_tags)
    question_list, chosen_prof_evals = search_data_to_q_list(search_data)
    chosen_questions = which_questions(question_list)
    return chosen_prof_evals, chosen_questions;

#------------------------For each response to a question (evaluation or eval for short), have a Eval object of the form:
#code = course code (string)
#prof = professor name
#question = question text (string)
#r_type = the type of response (string) as determined by first tag after <body> (either <table> or <a>)
#response = HTML of response

class Eval:
    def __init__(self, code, prof, question, r_type, response):
        self.code = code
        self.prof = prof
        self.question = question
        self.r_type = r_type
        self.response = response
        
#Organize in a dictionary of key = question text (string) and value = set of relevant Eval Objects

#Reminder: chosen_prof_evals = dictionary where keys = course codes and values = dictionary [keys=professor names and values=professor objects]

#Reminder: prof objects are structured as: name is prof name, quarter is the quarter (season year), and the eval is an eval dictionary of form: key = question, value = response

def check_response_type(response):
    if response.find('table') == None:
        return 'image'
    return 'table'

def check_build_eval_object(q_set, code, prof, question, eval_dict):
    if question in q_set:
        response = eval_dict[question]
        r_type = check_response_type(response)
        eval_object = Eval(code, prof, question, r_type, response)
        return eval_object
    return None

def append_to_dict_value(question_data, question, eval_object):
    value_copy = question_data[question].copy()
    value_copy.append(eval_object)
    question_data[question] = value_copy
    return question_data

def prof_to_dict_update(code, question_data, prof, prof_dict, q_set):
    prof_object = prof_dict[prof]
    eval_dict = prof_object.eval
    for question in eval_dict:
        eval_object = check_build_eval_object(q_set, code, prof, question, eval_dict)
        if eval_object == None:
            continue
        question_data = append_to_dict_value(question_data, question, eval_object)
    return question_data
    
def course_to_dict_update(q_set, code, chosen_prof_evals, question_data):
    prof_dict = chosen_prof_evals[code]
    for prof in prof_dict:
        question_data = prof_to_dict_update(code, question_data, prof, prof_dict, q_set)
    return question_data
    
def chosen_evals_to_dict_update(q_set, chosen_prof_evals, question_data):
    for code in chosen_prof_evals:
        question_data = course_to_dict_update(q_set, code, chosen_prof_evals, question_data)
    return question_data
    
def chosen_question_data(chosen_prof_evals, chosen_questions):
    q_set = set(chosen_questions)
    question_data = dict.fromkeys(chosen_questions, [])
    question_data = chosen_evals_to_dict_update(q_set, chosen_prof_evals, question_data)
    return question_data
    
#Take in the bs4 soup from course feedback data file and classes_set and perform the user interaction and data pulling to return the question_data

def search_to_data(soup, classes_set):
    chosen_prof_evals, chosen_questions = select_classes_profs_questions(soup, classes_set)
    question_data = chosen_question_data(chosen_prof_evals, chosen_questions)
    return question_data

#-----------------------VISUALIZE QUESTION DATA
#REMINDER: question_data is a dictionary of form:
    #key = question, value = list of Eval objects of form:
        #code = course code (string)
        #prof = professor name
        #question = question text (string)
        #r_type = the type of response (string) as determined by first tag after <body> (either 'table' or 'image')
        #response = HTML of response

def html_to_df(response):
    html_table = str(response)
    data_frame = pd.read_html(html_table)[0]
    return data_frame

def display_eval_table(eval_object):
    question = eval_object.question
    course_code = eval_object.code
    prof_name = eval_object.prof
    response = eval_object.response
    response_df = html_to_df(response)
    print('\nQUESTION: ' + question)
    print('PROFESSOR: ' + prof_name + '; COURSE: ' + course_code)
    print(tabulate(response_df, showindex=False))
    
def display_table_eval(question, question_data):
    eval_list = question_data[question]
    for eval_object in eval_list:
        print('\n')
        display_eval_table(eval_object)

def check_if_img_question(question, question_data):
    eval_list = question_data[question]
    sample_eval_object = eval_list[0]
    response_type = sample_eval_object.r_type
    if response_type == 'image':
        return True
    return False
    
def pull_img_src(eval_object):
    html = eval_object.response
    a_tag = html('a')[0]
    img_src = a_tag['href']
    return img_src
    
def build_img_eval_list(question, question_data):
    img_eval_list = question_data[question]
    for eval_object in img_eval_list:
        img_src = pull_img_src(eval_object)
        img_spec = io.imread(img_src)
        eval_object.response = img_spec
    return img_eval_list

def build_img_plot(question, img_eval_list):
    plt.figure()
    plt.subplots_adjust(wspace=0.2, hspace=0.2)
    plt.suptitle(question)
    plt.tight_layout()
    response_count = len(img_eval_list)
    # set number of columns
    ncols = 2
    # calculate number of rows
    nrows = response_count // ncols + (response_count % ncols > 0)
    for n in range(response_count):
        eval_object = img_eval_list[n]
        prof_name = eval_object.prof
        course_code = eval_object.code
        eval_img = eval_object.response
        ax = plt.subplot(nrows, ncols, n + 1)
        ax.imshow(eval_img)
        ax.axis('off')
        ax.set_title('PROFESSOR: ' + prof_name + '; COURSE: ' + course_code)
    plt.show()
    
def display_img_eval(question, question_data):
    img_eval_list = build_img_eval_list(question, question_data)
    build_img_plot(question, img_eval_list)

def display_reponses(question, question_data):
    if check_if_img_question(question, question_data):
        display_img_eval(question, question_data)
    else:
        display_table_eval(question, question_data)

def return_searched_feedback(question_data):
    for question in question_data:
        display_reponses(question, question_data)
        
def search_to_display(soup, classes_set):
    pd.options.display.max_rows = 50
    pd.options.display.max_columns = 50
    pd.options.display.max_colwidth = 999
    question_data = search_to_data(soup, classes_set)
    return_searched_feedback(question_data)
    user_engaged = yes_or_no('Would you like to do another search?')
    return user_engaged
    
#------------------BUILD CONSENT LOOP FOR REPEATED SEARCHES / USES

def feedback_portal(file_name):
    print('Please wait a minute while we load in the data')
    soup, classes_set = build_references(file_name)
    print("All done! Let's get started")
    user_engaged = True
    while user_engaged == True:
        user_engaged = search_to_display(soup, classes_set)
    print('Thanks for using this feedback portal tool! Please let me know any feedback you have.')
    

    


            
                
        
        

    
    
        
    
    
