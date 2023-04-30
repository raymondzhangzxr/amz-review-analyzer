from flask import Flask, render_template, request
import amzscraper as amz_scraper
import openaianalyzer as review_analyzer
import os


# get asin from the amazon url
def get_asin(url):
    # get the asin from the url
    asin = url.split("/dp/")[1].split("/")[0]
    # return the asin
    return asin


# check if the json file exists given asin
def is_json(asin):
    # check if the json file exists
    if os.path.exists(f"{asin}-reviews.json"):
        return True
    else:
        return False


app = Flask(__name__)


@app.route("/back", methods=["GET", "POST"])
def back():
    return render_template("home.html")


@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == "POST":
        search_term = request.form["product_name"]
        # Search Amazon with the search term
        searcher = amz_scraper.AmazonSearch(search_term)
        product_list = searcher.get_products()

        return render_template(
            "search.html", product_list=product_list, search_term=search_term
        )

    else:
        return render_template("home.html")


@app.route("/review-search/<string:asin>", methods=["POST"])
def review_search(asin):
    if request.method == "POST":

        product_asin = asin
        # check if the json file exists if not, scrape the reviews
        if not is_json(product_asin):
            # Scrape Amazon reviews
            scraper = amz_scraper.AmazonReviewScraper(product_asin, max_pages=2)
            scraper.get_all_reviews()
            # save the reviews to a json file as a copy
            scraper.save_to_json()
        else:
            print("File already exists")

        # Analyze reviews
        analyzer = review_analyzer.ReviewAnalyzer(product_asin)
        analyzer.load_reviews()
        summary = analyzer.generate_summary()
        pros_cons = analyzer.generate_pro_cons()
        buy_together = analyzer.generate_buy_together()

        recommendation = analyzer.generate_recommendation()

        return render_template(
            "result.html",
            product_url="https://www.amazon.com/dp/" + asin,
            summary=summary,
            pros_cons=pros_cons,
            recommendation=recommendation,
            buy_together=buy_together,
        )

    else:
        return render_template("home.html")


@app.route("/analyze", methods=["GET", "POST"])
def analyze():
    if request.method == "POST":
        product_url = request.form["product_url"]
        # From url, get the asin (product identifier)
        product_asin = get_asin(product_url)
        # check if the json file exists if not, scrape the reviews
        if not is_json(product_asin):
            # Scrape Amazon reviews
            scraper = amz_scraper.AmazonReviewScraper(product_asin, max_pages=2)
            scraper.get_all_reviews()
            # save the reviews to a json file as a copy
            scraper.save_to_json()
        else:
            print("File already exists")

        # Analyze reviews
        analyzer = review_analyzer.ReviewAnalyzer(product_asin)
        analyzer.load_reviews()
        summary = analyzer.generate_summary()
        pros_cons = analyzer.generate_pro_cons()
        buy_together = analyzer.generate_buy_together()

        recommendation = analyzer.generate_recommendation()

        return render_template(
            "result.html",
            product_url=product_url,
            summary=summary,
            pros_cons=pros_cons,
            recommendation=recommendation,
            buy_together=buy_together,
        )

    else:
        return render_template("home.html")


@app.route("/")
def home():
    return render_template("home.html")


if __name__ == "__main__":
    app.run(debug=True, port=4994)
