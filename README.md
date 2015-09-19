hackerrank-solutions
====================

Solutions to the original HackerRank challenges.

###Alpha

The SpaceX challenge required you to decode garbled strings that were encoded with different methods. 

The first 10,000 strings were encoded with a ROT cipher. Your task was to compute the rotation offset and decode the string. The decoded strings then had to be parsed into integers and submitted. For example, the decoded string "four thousand, three hundred and twenty-one" had to be parsed into 4321. This was easy enough to brute-force (with 25 possible offsets for each encoded string).

The following 1,000 strings would decode into a Wikipedia URL. However, it was difficult to tell if a decoded string is a valid URL. The brute-force approach is to try all 26 possible URLs until you receive a response. Once you retrieve the page content, you had to scrape the page to find the 4-digit code and submit it. I used [Beautiful Soup](http://www.crummy.com/software/BeautifulSoup/) to scrape the pages.