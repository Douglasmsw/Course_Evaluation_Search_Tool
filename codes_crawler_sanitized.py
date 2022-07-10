import util
import bs4
import requests


starting_url = "http://collegecatalog.uchicago.edu/thecollege/programsofstudy/"
limiting_domain = "http://collegecatalog.uchicago.edu"

#Checks if a given course tag in a list of course tags is the opener tag for a sequence, returns True or False
def is_sequence_opener(ls, i):
    tag = ls[i]
    next_tag = ls[i+1]
    #check if next item in tag list is a subsequence
    if util.is_subsequence(next_tag):
        #check if the original tag is a courseblock main
        if tag['class'] == ['courseblock', 'main']:
                return True
    return False
    
#Returns course code as a string
def course_code(tag):
    title_tag = tag.find('p', class_='courseblocktitle')
    title_text = title_tag.text
    title_text = title_text.replace('&nbsp;', ' ')
    title_text = title_text.replace('&#160;', ' ')
    title_text = title_text.replace(u'\xa0', u' ')
    title_ls = title_text.split('.')
    code = title_ls[0]
    code = code.split()
    code = (code[0], code[1])
    return code

#Goes through url HTML and returns list of course tags
def pull_courses(url):
    #first, get html for page
    req = util.get_request(url)
    if req is None:
        return []
    text = util.read_request(req)
    if text is None:
        raise ValueError('URL could not be converted to HTML file')
    #second, find all course tags on page
    soup = bs4.BeautifulSoup(text, "html5lib")
    courses = soup.find_all('div', class_= ["courseblock main", "courseblock subsequence"])
    return courses

#Goes through list of course tags and returns list of course codes
def course_info(course_list):
    codes = []
    for i in range(len(course_list)):
        course = course_list[i]
        #check if course tag is void and skip to avoid crashing
        if course is None:
            continue
        #check if course_list item is a sequence opener and skip loop if it is
        if i != len(course_list) - 1:
            if is_sequence_opener(course_list, i):
                continue
        #if not an opener it is a normal course so just append course code and description to course_content
        codes.append(course_code(course))
    return codes
    
#____________
    
#takes in starting url and finds all the urls on that page, returns them in a list
def get_urls(current_url):
    url_list = []
    url = current_url
    #first, get the html text for linked page
    req = util.get_request(url)
    #check to see if it is invalid, if so raise an error for investigation
    if req is None:
        raise ValueError('URL request failed')
    text = util.read_request(req)
    #similarly to above, check for error and raise for investigation
    if text is None:
        raise ValueError('URL could not be converted to HTML file')
    #second, find all <a> link tags and put their href url text into a list
    soup = bs4.BeautifulSoup(text, "html5lib")
    for a in soup.find_all('a', href=True):
        url_list.append(a['href'])
    return url_list


#Takes in list of urls on a page and returns valid urls to go to, call with starting url as current
def destinations(current_url, url_list, limiting_domain):
    paths = [current_url]
    for url in url_list:
        url = util.remove_fragment(url)
        #if url is absolute check if it is ok to follow
        if util.is_absolute_url(url):
            if url != current_url:
                if util.is_url_ok_to_follow(url, limiting_domain):
                    paths.append(url)
        #check if non-absolute is relative, if so convert and check if it is ok to follow
        elif not util.is_absolute_url(url):
            url = util.convert_if_relative_url(current_url, url)
            if url is not None:
                if url != current_url:
                    if util.is_url_ok_to_follow(url, limiting_domain):
                        paths.append(url)
    return paths
    
#_____________
        
def get_codes(starting_url, limiting_domain):
    #Gets list of urls on page
    url_list = get_urls(starting_url)
    #Creates list of valid urls including the starting url
    pages = destinations(starting_url, url_list, limiting_domain)
    all_codes = []
    for p in pages:
        #Get list of course tags from the page
        course_tags = pull_courses(p)
        #Get list of class codes from course tags
        codes = course_info(course_tags)
        #Add course codes to complete list
        all_codes += codes

    return all_codes
    
