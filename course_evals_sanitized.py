import selenium as se
from selenium import webdriver
from selenium.webdriver.common.by import By
import util
import codes_crawler as cc
import bs4
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import numpy as np
import os


starting_url = "http://collegecatalog.uchicago.edu/thecollege/programsofstudy/"
limiting_domain = "http://collegecatalog.uchicago.edu"

#go through course catalog and pull all the course codes in format (department, number)
def scrape_class_tuples(starting_url, limiting_domain):
    courses = cc.get_codes(starting_url, limiting_domain)
    return courses

def code_from_class_tuple(class_tuple):
    course_code = class_tuple[0] + ' ' + class_tuple[1]
    return course_code

#------------------ NAVIGATE TO COURSE FEEDBACK PAGE

feedback_url = 'https://coursefeedback.uchicago.edu/'

def verify_driver_path():
    device = input('What platform are you using, mac or pc?\n')
    if device == 'mac':
        user_driver = '/Users/Douglas/Desktop/Selenium_Web_Drivers/chromedriver'
        return user_driver, device;
    if device == 'pc':
        user_driver = ChromeDriverManager().install()
        return user_driver, device;
    print('Please redo input, either mac or pc, and remember that this is case-sensitive.')
    return verify_driver_path()

def nav(url, user_driver):
    browser = webdriver.Chrome(user_driver)
    browser.get(url)
    return browser

def login(browser):
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='text'][@id='okta-signin-username']")))
    username_input = browser.find_element(By.XPATH, "//input[@type='text'][@id='okta-signin-username']")

    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='password'][@id='okta-signin-password']")))
    password_input = browser.find_element(By.XPATH, "//input[@type='password'][@id='okta-signin-password']")
    
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='checkbox'][@name='remember'][@id='input41']")))
    remember_me_checkbox = browser.find_element(By.XPATH, "//input[@type='checkbox'][@name='remember'][@id='input41']")
    
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@class='button button-primary'][@type='submit'][@value='Sign In'][@id='okta-signin-submit']")))
    login_button = browser.find_element(By.XPATH, "//input[@class='button button-primary'][@type='submit'][@value='Sign In'][@id='okta-signin-submit']")
    
    action = ActionChains(browser)
    action.click(on_element=username_input).send_keys('USERNAME')
    action.click(on_element=password_input).send_keys('PASSWORD')
    action.click(on_element=remember_me_checkbox)
    action.click(on_element=login_button)
    action.perform()
    return browser
    
def auth_open(browser):
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//iframe[@frameborder='0'][@title='Duo Security']")))
    iframe = browser.find_element(By.XPATH, "//iframe[@frameborder='0'][@title='Duo Security']")
    browser.switch_to.frame(iframe)
    WebDriverWait(browser, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='checkbox'][@name='dampen_choice'][@value='1'][@tabindex='2']")))
    remember_me_checkbox = browser.find_element(By.XPATH, "//input[@type='checkbox'][@name='dampen_choice'][@value='1'][@tabindex='2']")
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='passcode-label row-label']")))
    sms_button = browser.find_element(By.XPATH, "//div[@class='passcode-label row-label']")
    action = ActionChains(browser)
    action.click(on_element=remember_me_checkbox)
    action.move_to_element(sms_button).click()
    action.perform()
    return browser
    
def reset_sms_codes(browser, sms_input, login_button):
    action = ActionChains(browser)
    print('SMS Codes need to be reset')
    WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@id='message'][@class='btn'][@tabindex='100']")))
    new_codes_button = browser.find_element(By.XPATH, "//button[@id='message'][@class='btn'][@tabindex='100']")
    browser.execute_script("arguments[0].scrollIntoView();", new_codes_button)
    action.click(on_element=new_codes_button).perform()
    print('New Codes sent to phone, update after execute')
    action.click(on_element=sms_input).send_keys('123456').perform()
    action.click(on_element=login_button).perform()
    WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='btn-dismiss medium-or-smaller']")))
    dismiss_button = browser.find_element(By.XPATH, "//button[@class='btn-dismiss medium-or-smaller']")
    browser.execute_script("arguments[0].scrollIntoView();", dismiss_button)
    action.click(on_element=dismiss_button).perform()
    call_button = browser.find_element(By.XPATH, "//div[@class='row-label phone-label']")
    print('Calling now')
    action.move_to_element(call_button).click().perform()
    time.sleep(15)
    #browser.switch_to.default_content()
    #WebDriverWait(browser, 10).until(
    #    EC.presence_of_element_located((By.ID, "nav-catalog-tab")))
    return browser

def authenticate(browser):
    action = ActionChains(browser)
    sms_codes = ['PASSCODES']
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//input[@type='text'][@class='passcode-input'][@aria-label='passcode'][@tabindex='2']")))
    sms_input = browser.find_element(By.XPATH, "//input[@type='text'][@class='passcode-input'][@aria-label='passcode'][@tabindex='2']")
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//button[@tabindex='2'][@type='submit'][@id='passcode']")))
    login_button = browser.find_element(By.XPATH, "//button[@tabindex='2'][@type='submit'][@id='passcode']")
    code_hint = browser.find_element(By.XPATH, "//input[@name='next-passcode'][@type='hidden']").get_attribute("value")
    for code in sms_codes:
        if code[0] == code_hint:
            sms_code = code
            break
    try:
        sms_code
    except:
        browser = reset_sms_codes(browser, sms_input, login_button)
        return browser
    else:
        action.click(on_element=sms_input).send_keys(sms_code)
        action.click(on_element=login_button)
        action.perform()
        return browser
 
def nav_log(feedback_url, user_driver):
    browser = nav(feedback_url, user_driver)
    browser = login(browser)
    return browser

def nav_catalog_tab(browser):
    browser.switch_to.default_content()
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.ID, "nav-catalog-tab")))
    nav_tab = browser.find_element(By.XPATH, "//a[@id='nav-catalog-tab'][@data-toggle='tab'][@href='#nav-catalog'][@role='tab']")
    action = ActionChains(browser)
    action.click(on_element=nav_tab)
    action.perform()
    return browser

def nav_auth(feedback_url, user_driver):
    browser = nav_log(feedback_url, user_driver)
    time.sleep(5)
    browser = auth_open(browser)
    time.sleep(5)
    browser = authenticate(browser)
    browser = nav_catalog_tab(browser)
    return browser

#---------------NAVIGATE TO A GIVEN COURSE'S FEEDBACK PAGE

def dept_search(browser, class_tuple):
    action = ActionChains(browser)
    try:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@class='chosen-single chosen-default']")))
        dept_drop_menu = browser.find_element(By.XPATH, "//div[@class='chosen-container chosen-container-single'][@id='catalogSubject_chosen']")
        drop_type = 'input'
    except:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.XPATH, "//select[@class='custom-select form-control chosen-select']")))
        dept_drop_menu = browser.find_element(By.XPATH, "//div[@class='chosen-container chosen-container-single'][@id='catalogSubject_chosen']")
        drop_type = 'select'
    action.move_to_element(dept_drop_menu).click().send_keys(class_tuple[0])
    action.perform()
    return browser#, drop_type;

def dropdown_select(browser, class_tuple):
    action = ActionChains(browser)
    dept = class_tuple[0]
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@class='chosen-drop']/ul/li")))
    drop_items = browser.find_elements(By.TAG_NAME, 'em')
    for item in drop_items:
        if item.text == dept:
            drop_select = item
            break
    action.move_to_element(drop_select).click().perform()
    return browser
    
def dropdown_match_dept(browser, class_tuple):
    dept = class_tuple[0]
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//div[@id='catalogSubject_chosen']/a/span")))
    dropdown_box_text = browser.find_element(By.XPATH, "//div[@id='catalogSubject_chosen']/a/span").text
    current_dept_selected = dropdown_box_text.split()[0]
    if current_dept_selected == dept:
        return True
    else:
        return False
    
def course_num_search(browser, class_tuple):
    action = ActionChains(browser)
    class_num_input = browser.find_element(By.XPATH, "//input[@class='form-control'][@id='catalogNumber'][@name='CourseNumber']")
    action.click(on_element=class_num_input).send_keys(class_tuple[1]).perform()
    return browser

def clear_num_search(browser):
    action = ActionChains(browser)
    class_num_input = browser.find_element(By.XPATH, "//input[@class='form-control'][@id='catalogNumber'][@name='CourseNumber']")
    action.double_click(on_element=class_num_input).send_keys(Keys.BACKSPACE).perform()
    return browser

def press_search(browser):
    action = ActionChains(browser)
    class_num_input = browser.find_element(By.XPATH, "//input[@class='form-control'][@id='catalogNumber'][@name='CourseNumber']")
    action.click(on_element=class_num_input).send_keys(Keys.ENTER).perform()
    return browser
    
def in_dept_search(browser, class_tuple):
    browser = clear_num_search(browser)
    browser = course_num_search(browser, class_tuple)
    browser = press_search(browser)
    return browser

def nav_class_evals(browser, class_tuple):
    browser = dept_search(browser, class_tuple)
    browser = dropdown_select(browser, class_tuple)
    browser = clear_num_search(browser)
    browser = course_num_search(browser, class_tuple)
    browser = press_search(browser)
    return browser
        
#------------ GET PROFESSOR INFO AND URL OF MOST RECENT EVALUATION
        
def pull_html(browser):
    html = browser.page_source
    soup = bs4.BeautifulSoup(html, "lxml")
    return soup

def pull_search_results(soup):
    results_table = soup.find('table', class_='data-table', id='evalSearchResults')
    if results_table == None:
        raise Exception('No feedback for this course')
    results = results_table.find_all('tbody')[0]
    search_results = results.find_all('tr')
    return search_results

def pull_prof_names(search_results):
    names = set()
    for tag in search_results:
        prof_name = tag.find('td', class_='instructor').text
        names.add(prof_name)
    return names

def pull_prof_evals(search_results, target_name):
    prof_evals = []
    for tag in search_results:
        prof_name = tag.find('td', class_='instructor').text
        if prof_name == target_name:
            prof_evals.append(tag)
    return prof_evals

def pull_eval_quart(eval):
    quart = eval.find('td', class_=['quarter sorting_1', 'quarter']).text
    quart = quart.split()
    quart = quart[0]
    return quart
    
def pull_str_quart(eval):
    quart = eval.find('td', class_=['quarter sorting_1', 'quarter']).text
    quart = quart.split()
    quart = quart[1] + ' ' + quart[2]
    return quart
    
def quart_to_int(quart):
    quart = quart.replace('(','')
    quart = quart.replace(')','')
    quart = int(quart)
    return quart
    
def quart_to_str(quart):
    quart = '(' + str(quart) + ')'
    return quart

def pull_most_recent_quarter(prof_evals):
    quarters = []
    for eval in prof_evals:
        quart = pull_eval_quart(eval)
        quart = quart_to_int(quart)
        quarters.append(quart)
    most_recent = max(quarters)
    most_recent_quarter = quart_to_str(most_recent)
    return most_recent_quarter

def most_recent_eval(prof_evals):
    most_recent_quarter = pull_most_recent_quarter(prof_evals)
    for eval in prof_evals:
        quart = pull_eval_quart(eval)
        if quart == most_recent_quarter:
            str_quart = pull_str_quart(eval)
            return eval, str_quart;

def pull_relevant_prof_eval(search_results, target_name):
    prof_evals = pull_prof_evals(search_results, target_name)
    relevant_prof_eval, quarter = most_recent_eval(prof_evals)
    return relevant_prof_eval, quarter;

def pull_eval_url(eval):
    title_tag = eval.find('td', class_='title')
    link_tag = title_tag.find('a')
    url = link_tag['href']
    return url
    
def nav_new_tab(browser, url):
    browser.execute_script("window.open('');")
    browser.switch_to.window(browser.window_handles[1])
    browser.get(url)
    return browser

#----------------- EXTRACT EVALUATION INFORMATION: DICTIONARY OF KEY:QUESTION, VALUE:RESPONSES
 
#REMINDER:
#def pull_html(browser):
#    html = browser.page_source
#    soup = bs4.BeautifulSoup(html, "lxml")
#    return soup
    
def pull_eval_html(soup):
    report_blocks = soup.find_all('div', class_='report-block')
    return report_blocks
   
def combine_attributes(attribute):
    if isinstance(attribute, list):
        if len(attribute) > 1:
            attribute = attribute[0] + ' ' + attribute[1]
        else:
            attribute = attribute[0]
    return attribute

def id_attribute(attribute):
    if attribute == 'SpreadsheetBlockRow TableContainer':
        return 'spreadsheet'
    if attribute == 'CommentBlockRow TableContainer':
        return 'comments'
    if attribute == 'FrequencyBlockRow':
        return 'graphic'
    else:
        raise ValueError('Unable to identify eval type for: ' + rep_block.text)

def question_type(rep_block):
    #either dataframe with 'SpreadsheetBlockRow TableContainer', 'CommentBlockRow TableContainer', or 'FrequencyBlockRow' in a div tag
    tags = rep_block.find_all('div', {'class' : True})
    attribute_ids = [tag['class'] for tag in tags]
    target_identifiers = {'SpreadsheetBlockRow TableContainer', 'CommentBlockRow TableContainer', 'FrequencyBlockRow'}
    for attribute in attribute_ids:
        attribute = combine_attributes(attribute)
        if attribute in target_identifiers:
            type = id_attribute(attribute)
            return type
        
def spreadsheet_eval_html(rep_block):
    html = str(rep_block.find('table'))
    return html

def spreadsheet_eval_question(rep_block):
    question_check = rep_block.find_all('h4')
    if len(question_check) != 0:
        question = question_check[0].find('span').text
        if len(question.split()) > 3:
            return question
        else:
            return question + ' agreement scores. ("Facilitated discussions that were engaging and useful; Challenged you to learn; etc.")'
    else:
        return 'Course statement agreement scores. ("This course challenged me intellectually; strongly disagree, disagree, neutral, agree, strongly agree; etc.")'
        
def spreadsheet_question_response(rep_block):
    question = spreadsheet_eval_question(rep_block)
    html = spreadsheet_eval_html(rep_block)
    return question, html
    
def comments_eval_html(rep_block):
    html = str(rep_block.find('table'))
    return html
    
def comments_eval_question(rep_block):
    question = rep_block.find('span').text
    return question

def comments_question_response(rep_block):
    question = comments_eval_question(rep_block)
    html = comments_eval_html(rep_block)
    return question, html
    
def graphic_eval_file(rep_block):
    url = 'https://uchicago.bluera.com/' + rep_block.find('img')['src']
    return url
    
def graphic_eval_question(rep_block):
    question = rep_block.find('span').text
    return question

def graphic_question_response(rep_block):
    question = graphic_eval_question(rep_block)
    url = graphic_eval_file(rep_block)
    return question, url

def eval_question_response(rep_block):
    type = question_type(rep_block)
    if type == 'spreadsheet':
        question, response = spreadsheet_question_response(rep_block)
        return question, response;
    if type == 'comments':
        question, response = comments_question_response(rep_block)
        return question, response;
    if type == 'graphic':
        question, response = graphic_question_response(rep_block)
        return question, response;
    else:
        raise ValueError('Unable to identify the type of: ' + rep_block.text)
    
def dict_from_report_blocks(report_blocks):
    dict = {}
    for rep_block in report_blocks:
        question, response = eval_question_response(rep_block)
        dict[question] = response
    return dict

def make_eval_dict(browser, eval):
    url = pull_eval_url(eval)
    browser = nav_new_tab(browser, url)
    soup = pull_html(browser)
    report_blocks = pull_eval_html(soup)
    dict = dict_from_report_blocks(report_blocks)
    browser.close()
    browser.switch_to.window(browser.window_handles[0])
    return dict
    
#------------------- EXTRACT COURSE INFO AND PUT IT INTO COURSE AND PROF OBJECTS. THERE SHOULD BE A DICTIONARY WHERE KEYS ARE COURSE CODES AND VALUES ARE COURSE OBJECTS
  
#code has course code and profs is a dictionary of form: key = prof name, value = prof object
class Course:
    def __init__(self, code, profs):
        self.code = code
        self.profs = profs

#name is prof name, quarter is the quarter (season year), and the eval is an eval dictionary of form: key = question, value = response
class Prof:
    def __init__(self, name, eval, quarter):
        self.name = name
        self.quarter = quarter
        self.eval = eval

def make_prof_object(browser, search_results, target_name):
    eval, quarter = pull_relevant_prof_eval(search_results, target_name)
    eval_dict = make_eval_dict(browser, eval)
    prof_object = Prof(target_name, eval_dict, quarter)
    return prof_object
   
def make_prof_dict(browser, search_results, prof_names):
    prof_dict = {}
    for name in prof_names:
        prof_object = make_prof_object(browser, search_results, name)
        prof_dict[name] = prof_object
    return prof_dict
   
def make_course_object(browser, class_tuple):
    course_code = code_from_class_tuple(class_tuple)
    soup = pull_html(browser)
    search_results = pull_search_results(soup)
    prof_names = pull_prof_names(search_results)
    prof_dict = make_prof_dict(browser, search_results, prof_names)
    course_object = Course(course_code, prof_dict)
    return course_object

#-------------- LOOP OVER CLASS TUPLES TO CREATE INDEX: DICTIONARY IN FORM: KEY = COURSE CODE, VALUE = COURSE OBJECT
            
def search_to_course_object(browser, class_tuple):
    if dropdown_match_dept(browser, class_tuple) == False:
        browser = nav_class_evals(browser, class_tuple)
        course_object = make_course_object(browser, class_tuple)
        return course_object
    if dropdown_match_dept(browser, class_tuple) == True:
        browser = in_dept_search(browser, class_tuple)
        course_object = make_course_object(browser, class_tuple)
        return course_object

def loop_index_builder(loop_index, courses, user_driver):
    run_index = {}
    try:
        browser = nav_auth(feedback_url, user_driver)
    except:
        browser = nav_auth(feedback_url, user_driver)
    for i in loop_index:
        class_tuple = courses[i]
        course_code = code_from_class_tuple(class_tuple)
        try:
            course_object = search_to_course_object(browser, class_tuple)
        except:
            course_object = Course(course_code, None)
        run_index[course_code] = course_object
    browser.quit()
    return run_index
    
def build_index(user_driver):
    print('Scraping course codes')
    courses = scrape_class_tuples(starting_url, limiting_domain)
    print('Codes scraped')
    limiting_index = len(courses)
    start_index = 0
    loop_index = range(start_index, limiting_index)
    index = loop_index_builder(loop_index, courses, user_driver)
    return index
    
#----------------------SERIALIZE THE INDEX INTO AN HTML FILE
#STEP ONE - MAKE ALL HTML INTO A BIG STRING
#REMINDER:
#class Course:
    #def __init__(self, code, profs):
     #   self.code = code
      #  self.profs = profs

#name is prof name, quarter is the quarter (season year), and the eval is an eval dictionary of form: key = question, value = response
#class Prof:
 #   def __init__(self, name, eval, quarter):
  #      self.name = name
   #     self.quarter = quarter
    #    self.eval = eval

#Courses denoted with div tags of form <div class=course, id=course_code, style=indicate if there is feedback for course>
#Profs denoted with div tags of form <div class="prof" id="prof_name" title="course_code" tabindex="quarter">

def prof_div_attributes(prof_object, course_code):
    class_ = 'class="prof"'
    id = 'id="' + prof_object.name + '"'
    title = 'title="' + course_code + '"'
    tab_index = 'tabindex="' + prof_object.quarter + '"'
    attributes = class_ + ' ' + id + ' ' + title + ' ' + tab_index
    return attributes
    
def check_if_no_feedback(course_object):
    if course_object.profs == None:
        return True
    return False
    
def course_div_attributes(course_object):
    class_ = 'class="course"'
    id = 'id="' + course_object.code + '"'
    if check_if_no_feedback(course_object):
        style = 'style="no_feedback"'
    else:
        style = 'style="feedback"'
    attributes = class_ + ' ' + id + ' ' + style
    return attributes

def table_or_link(response):
    if response[0] == '<':
        return 'table'
    if response[0] == 'h':
        return 'link'
    return None

def link_to_tag(response):
    tag = '<a href="' + response + '"></a>\n'
    return tag

def response_to_html(response):
    response_type = table_or_link(response)
    if response_type == None:
        return None, response_type;
    if response_type == 'table':
        html = response + '\n'
        return html, response_type;
    if response_type == 'link':
        html = link_to_tag(response)
        return html, response_type;

def question_to_html(question, response):
    response_html, question_type = response_to_html(response)
    if response_html == None:
        return None
    open_tag = '<div class="question" id="' + question + '" style="' + question_type + '">\n'
    close_tag = '</div>\n'
    html = open_tag + response_html + close_tag
    return html

def eval_dict_to_html(prof_object, course_code):
    eval = prof_object.eval
    html = ''
    for question in eval:
        response = eval[question]
        question_html = question_to_html(question, response)
        if question_html == None:
            raise ValueError('Unable to id response type of question: ' + question + ' for course: ' + course_code)
        html += question_html
    return html

def prof_to_html(prof_object, course_code):
    eval_html = eval_dict_to_html(prof_object, course_code)
    attributes = prof_div_attributes(prof_object, course_code)
    open_tag = '<div ' + attributes + '>\n'
    close_tag = '</div>\n'
    html = open_tag + eval_html + close_tag
    return html

def prof_dict_to_html(prof_dict, course_code):
    html = ''
    for prof in prof_dict:
        prof_object = prof_dict[prof]
        prof_html = prof_to_html(prof_object, course_code)
        html += prof_html
    return html
    
def no_feedback_to_html(course_object):
    attributes = course_div_attributes(course_object)
    open_tag = '<div ' + attributes + '>\n'
    close_tag = '</div>\n'
    course_code = course_object.code
    prof_dict_html = '<p>There is no feedback for this course</p>\n'
    html = open_tag + prof_dict_html + close_tag
    return html

def course_to_html(course_object):
    attributes = course_div_attributes(course_object)
    open_tag = '<div ' + attributes + '>\n'
    close_tag = '</div>\n'
    course_code = course_object.code
    prof_dict = course_object.profs
    prof_dict_html = prof_dict_to_html(prof_dict, course_code)
    html = open_tag + prof_dict_html + close_tag
    return html

def index_dict_to_html(index):
    html = ''
    for course in index:
        course_object = index[course]
        if check_if_no_feedback(course_object):
            course_html = no_feedback_to_html(course_object)
        else:
            course_html = course_to_html(course_object)
        html += course_html
    return html

def index_to_html(index):
    open_tags = '<html>\n<head>\n<title>\nCourse Evaluation Index In HTML Format\n</title>\n</head>\n<body>'
    close_tags = '</body>\n</html>'
    index_html = index_dict_to_html(index)
    html = open_tags + index_html + close_tags
    return html

def html_to_file(file_name, html, device):
    cwd = os.getcwd()
    if device == 'pc':
        file_path = cwd + '\\' + file_name
    else:
        file_path = cwd + '/' + file_name
    html_file = open(file_path, 'w', encoding='utf-8')
    html_file.write(html)
    html_file.close()
    return 'Check for your file!'
    
def build_index_file():
    file_name = 'course_evalutations_' + input('Input the current date below in format: MM_DD_YYYY:\n') + '.txt'
    user_driver, device = verify_driver_path()
    index = build_index(user_driver)
    index_html = index_to_html(index)
    html_to_file(file_name, index_html, device)
    return index

#--------------------READING FILE IN FOR FRONT END
#REMINDER:
#Courses denoted with div tags of form <div class=course, id=course_code, style=indicate if there is feedback for course>
#Profs denoted with div tags of form <div class="prof" id="prof_name" title="course_code" tabindex="quarter">

def index_file_to_soup(file_name):
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
    courses = soup.find_all('div', class_='course', style='feedback')['id']
    courses = set(courses)
    classes_set = de_list_items(courses)
    return classes_set
    
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

def class_tuples_to_set(classes_set):
    return_set = set()
    for tup in classes_set:
        joined_str = ' '.join(tup)
        return_set.add(joined_str)
    return return_set
    
#----------------------------PULLING RELEVANT COURSE OBJECTS BASED ON SEARCH LIST
    
    
    

    

    
    
        
    
