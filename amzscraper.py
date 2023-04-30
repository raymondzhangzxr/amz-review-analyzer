from bs4 import BeautifulSoup
import pandas as pd
import requests
import logging
import json

# configure the logger
logging.basicConfig(
    filename="amazon-scraper.log",
    level=logging.INFO,
    format="%(asctime)s:%(levelname)s:%(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

# A base class for the scraper and searcher, contains the common methods
# 1. make_request: makes a request to the url
# 2. get_soup: returns the soup object for the url


class AmazonWebRobot:
    def __init__(self) -> None:
        self.splash_host = "http://localhost:8050/render.html"
        self.amazon_link_prefix = "https://www.amazon.com"

    def make_request(self, url):
        # make a request to the url, Catch any exceptions
        try:
            # Get the page using the splash server
            response = requests.get(self.splash_host, params={"url": url, "wait": 2})
        except requests.exceptions.RequestException:
            logging.warning(f"HTTP Error for link {url}")
            return
        # check if the request is successful, return the response
        if response.status_code == 200:
            return response

    # get the soup object
    def get_soup(self, url):
        # make a request to the url
        r = self.make_request(url)
        # check if the request is successful, if not throw exception
        if not r:
            logging.warning(f"Request to {url} failed for link {url}")
            raise Exception("HTTP Request Failed")
        # create a soup object
        soup = BeautifulSoup(r.text, "html.parser")
        # return the soup object
        return soup


class AmazonReviewScraper(AmazonWebRobot):
    def __init__(self, asin: str, max_pages: int = 1) -> None:
        # Call the super class constructor
        super().__init__()
        self.asin = asin
        # Get the url to the all reviews page; filered by the more recent reviews
        self.initial_url = f"https://www.amazon.com/product-reviews/{self.asin}/ref=cm_cr_arp_d_viewopt_srt?sortBy=recent&pageNumber=1"
        # The list to store the reviews as dict for json outputs
        self.review_list = []
        # The list for chatgpt inputs, all the reviews in one string separated by new lines
        self.chatgpt_input = []
        self.max_pages = max_pages
        self.product_name = None
        # Log the asin, the initial url, and the splash host
        logging.info(
            f"Scraper Initialized for asin: {self.asin}, initial url: {self.initial_url}, splash host: {self.splash_host}"
        )

    # extract the reviews from soup
    def get_reviews_from_a_page(self, soup):
        # get the product name
        if not self.product_name:
            self.product_name = soup.find(
                "a", {"data-hook": "product-link"}
            ).text.strip()
        print(self.product_name)

        # get all the reviews
        reviews = soup.find_all("div", {"data-hook": "review"})
        # loop through the reviews
        try:
            for review in reviews:
                review_dict = {
                    # product name; getting rid of the header
                    # "product_name": soup.title.text.replace(
                    #     "Amazon.com: Customer reviews: ", ""
                    # ).strip(),
                    # get the title of the review, check if it exists first
                    "title": review.find(
                        "a", {"data-hook": "review-title"}
                    ).text.strip(),
                    # Get the star rating in float
                    "star_rating": float(
                        review.find("i", {"data-hook": "review-star-rating"})
                        .text.replace("out of 5 stars", "")
                        .strip()
                    ),
                    # Get the body of the review
                    "body": review.find("span", {"data-hook": "review-body"})
                    .text.replace("\n", "")
                    .strip(),
                }
                # append the review to the review list
                self.review_list.append(review_dict)
                # append the review to the chatgpt input
                self.chatgpt_input.append(
                    "Review Title: "
                    + review_dict["title"]
                    + " Review Rating: "
                    + str(review_dict["star_rating"])
                    + " Review Body: "
                    + review_dict["body"]
                )
        except:
            pass

    # get the next review page
    def get_next_page_url(self, soup):
        page = soup.find("ul", {"class": "a-pagination"})
        if not page:
            return None
        # check if there is a next page
        if not page.find("li", {"class": "a-disabled a-last"}):
            next_page = (
                self.amazon_link_prefix
                + page.find("li", {"class": "a-last"}).find("a")["href"]
            )
            return next_page
        else:
            # if there is no next page, return None
            return None

    def get_all_reviews(self):
        # get the first page of reviews
        page_num = 1
        soup = self.get_soup(self.initial_url)
        # get the reviews from the first page
        self.get_reviews_from_a_page(soup)
        # get the next page url
        next_page_url = self.get_next_page_url(soup)
        # log the progress of the scraper, page number, and the size of the review list
        print(
            f"Scraping page {page_num} for {self.asin}, size of review list: {len(self.review_list)}"
        )
        logging.info(
            f"Scraping page {page_num} for {self.asin}, size of review list: {len(self.review_list)}"
        )
        # loop through the pages
        while next_page_url and page_num < self.max_pages:
            page_num += 1
            # get the next page
            soup = self.get_soup(next_page_url)
            # get the reviews from the page
            self.get_reviews_from_a_page(soup)
            # get the next page url
            next_page_url = self.get_next_page_url(soup)
            print(
                f"Scraping page {page_num} for {self.asin}, size of review list: {len(self.review_list)}"
            )
            logging.info(
                f"Scraping page {page_num} for {self.asin}, size of review list: {len(self.review_list)}"
            )

    # save the reviews to a json file
    def save_to_json(self):
        # save product name to the begining of the json
        self.review_list.insert(0, {"product_name": self.product_name})
        with open(self.asin + "-reviews.json", "w") as f:
            json.dump(self.review_list, f)

    # Get chatgpt input
    def get_chatgpt_input(self):
        return self.chatgpt_input


# A class to search product on amazon and return the top k asins
class AmazonSearch(AmazonWebRobot):
    def __init__(self, search_terms) -> None:
        # Call the super class constructor
        super().__init__()
        self.serch_terms = search_terms
        self.search_url = self.generate_search_url()
        # get the soup object
        self.soup = self.get_soup(self.search_url)
        self.product_list = []

    def is_asin(self, asin):
        # check if the asin is valid
        if len(asin) != 10:
            return False
        else:
            return True

    def generate_search_url(self):
        # generate the search url
        # strip the search terms and combine them by +
        self.serch_terms = "+".join(self.serch_terms.strip().split(" "))
        search_url = f"https://www.amazon.com/s?k={self.serch_terms}&ref=nb_sb_noss_2"
        return search_url

    def get_products(self):
        # find all the products on the page
        products = self.soup.find_all("div", {"data-component-type": "s-search-result"})
        # save product name, link, price, and asin in a dictionary

        for product in products:
            try:
                link = product.find(
                    "a",
                    {
                        "class": "a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal"
                    },
                )["href"]
                # If the can not find the link, try with a different class name
                if not link:
                    link = product.find(
                        "a",
                        {
                            "class": "a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal"
                        },
                    )["href"]

                # Ignore promotion items, the promoted item does not have an asin at 3rd index
                asin = link.split("/")[3]
                if not self.is_asin(asin):
                    continue

                title = product.find(
                    "span", {"class": "a-size-medium a-color-base a-text-normal"}
                )
                if not title:
                    title = product.find(
                        "span", {"class": "a-size-base-plus a-color-base a-text-normal"}
                    )
                title = title.text.strip()

                price = product.find("span", {"class": "a-offscreen"}).text.strip()

                rating = float(
                    product.find("span", {"class": "a-icon-alt"})
                    .text.replace("out of 5 stars", "")
                    .strip()
                )
                image_link = product.find("img", {"class": "s-image"})["src"]
                # save in a dictionary and then append the dict to the product list
                product_dict = {
                    "title": title,
                    "link": self.amazon_link_prefix + link,
                    "price": price,
                    "asin": asin,
                    "rating": rating,
                    "image_link": image_link,
                }
                self.product_list.append(product_dict)

            except:
                pass
        # sort the product list by rating
        return sorted(self.product_list, key=lambda x: x["rating"], reverse=True)

