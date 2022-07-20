# Course Crawler
This project is from when I was trying to learn webscraping. I wanted to scrape and store the class feedback question-by-question and make a tool (to be built) so it is easier to view and compare class-specific professor evaluations. 

There are 2 different "scraping scripts" contained within this:

1) **Codes Crawler** -- This script opens up the UChicago course catalog main page and uses Beautiful Soup to: <br />
   a) Determine which links on the page lead to a department catalog page <br />
   b) Open these pages (using requests) and pull the page html <br />
   c) Find and save the unique course codes for every class
   
2) **Course Evals** -- This scripts uses the course codes returned by the codes crawler, Beautiful Soup, and Selenium to: <br />
  a) Navigate to the course feedback portal (all login information sanitized in uploaded files) <br />
  b) Search each unique course code <br />
  c) Go through the professors for each class and identify their most recent evaluation <br />
  d) Open the most recent evalutions for each professor who taught each class and pull the data on each question and response <br />
  e) Serialize the class, professor, question, and response data in HTML format (lots of nesting in tree data structure) and write it into a file
  
I am currently working on a front_end file that unpacks the serialized data and allows you to interact with your terminal to request comparison 
graphics of specific review questions for specific professors in specific courses. Needless to say it is taking longer than expected [working full-time
takes away code time :(].

*Note* -- The Util file is used to help the Codes Crawler determine which of the links leads toa department catalog and which are not useful for my purposes.
