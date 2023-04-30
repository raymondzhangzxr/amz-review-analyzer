import json
import openai

# Use openai read the reviews' json file, and generate a review summary and make recommendations
class ReviewAnalyzer:
    def __init__(self, asin: str) -> None:
        self.asin = asin
        self.reviews = []
        self.summary = ""
        self.recommendation = ""
        openai.api_key = "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"

    def load_reviews(self):
        with open(self.asin + "-reviews.json", "r") as f:
            reviews = json.load(f)
        # Put the reviews title, rating, and body to one string to help chatgpt, and put it in a list
        self.product_name = reviews[0]["product_name"]
        self.reviews = [
            "Review Title: "
            + review["title"]
            + " Review Rating: "
            + str(review["star_rating"])
            + " Review Body: "
            + review["body"]
            for review in reviews[1:]  # the first one is the product name
        ]

    def generate_summary(self):
        prompt = (
            "Can you summarize the reviews for "
            + self.product_name
            + " ? Here are the reviews:"
            + "\n\n".join(self.reviews).join(".")
        )

        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=0.5,
            max_tokens=100,
            n=1,
            stop=None,
            timeout=30,
            frequency_penalty=0,
            presence_penalty=0,
        )
        summary = response.choices[0].text.strip()

        return summary

    def generate_pro_cons(self):
        prompt = (
            "Based on the reviews for "
            + self.product_name
            + ", can you 1. list three pros and 2. list three cons mentioned by customers? Here are the reviews: "
            + "\n\n".join(self.reviews).join(".")
        )
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=0.5,
            max_tokens=200,
            n=1,
            stop=None,
            timeout=30,
            frequency_penalty=0,
            presence_penalty=0,
        )

        output = response.choices[0].text.strip()

        return output

    def generate_recommendation(self):
        prompt = (
            "Based on the reviews of "
            + self.product_name
            + ", would you recommend to buy it? Here are the reviews: "
            + "\n\n".join(self.reviews).join(".")
        )
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=0.5,
            max_tokens=100,
            n=1,
            stop=None,
            timeout=30,
            frequency_penalty=0,
            presence_penalty=0,
        )

        output = response.choices[0].text.strip()
        return output

    def generate_buy_together(self):
        prompt = (
            "Can you recommend a product that I should buy together with "
            + self.product_name
            + "?"
            + "\n\n".join(self.reviews).join(".")
        )
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=0.5,
            max_tokens=200,
            n=1,
            stop=None,
            timeout=30,
            frequency_penalty=0,
            presence_penalty=0,
        )

        output = response.choices[0].text.strip()

        return output
