import os
import asyncio
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key = OPENAI_API_KEY)
async def generate_summary(user):
    completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "developer", "content": """You are an expert in summarizing the transcript of telephonic conversation. 
         The key points of summary involves:
            - Key Discussion Points
            - Actions Taken (e.g., cancellation, refund, trial extension)
            - Attorney Listings Provided (if applicable)
            - Relevant Information or Resources Shared

         """},
        {
            "role": "user",
            "content": f"Generate the summary of the following Conversation: \n\n {user}"
        }
    ]
)
    summary = completion.choices[0].message.content
    return summary


aclient = AsyncOpenAI()
async def async_generate_summary(user):
    response = await aclient.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "developer", 
                "content": (
                    "You are an expert in summarizing the transcript of telephonic conversation. "
                    "The key points of summary involves:\n"
                    "- Key Discussion Points\n"
                    "- Actions Taken (e.g., cancellation, refund, trial extension)\n"
                    "- Attorney Listings Provided (if applicable)\n"
                    "- Relevant Information or Resources Shared\n"
                )
            },
            {
                "role": "user",
                "content": f"Generate the summary of the following Conversation: \n\n {user}"
            }
        ]
    )
    summary = response.choices[0].message.content
    return summary

async def main():
    path = "transcripts/call_transcript_CA4d27237f9256dd4ef1c977c23ece83c4.txt"
    with open(path, 'r') as file:
        transcript = file.read()
    summary = await async_generate_summary(transcript)
    print(summary)

# # Run the async main function
# asyncio.run(main())


import aiohttp
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_URL = "https://legalaibots-backend-vy7ua.ondigitalocean.app"

async def get_customer_data(phone: str):
    """
    Asynchronously fetch customer data from the Voice-Bot API.
    
    :param phone: Customer phone number (e.g., "+923114663661" or "923114663661")
    :return: JSON response with customer details or an error message
    """
    url = f"{BASE_URL}/api/voice-bot/getCustomerData"

    # Ensure phone number is formatted correctly
    formatted_phone = phone.lstrip("+")  # Remove '+' if present
    
    # Construct the request URL manually to prevent encoding issues
    request_url = f"{url}?phone={formatted_phone}"
    
    try:
        logging.info(f"Fetching data for phone: {formatted_phone}")
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(request_url) as response:
                data = await response.json()
                
                # Handle cases where no data is found
                if "response" not in data or not data["response"]:
                    logging.warning("No customer data found for the given phone number.")
                    return {"error": "Customer data not found"}
                
                return data

    except asyncio.TimeoutError:
        logging.error("Request timed out while fetching customer data.")
        return {"error": "Request timed out"}
    except aiohttp.ClientResponseError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
        return {"error": f"HTTP error: {http_err}"}
    except aiohttp.ClientError as req_err:
        logging.error(f"Request failed: {req_err}")
        return {"error": f"Request error: {req_err}"}

import requests

# def billing_extension(extension_days: str, phone: str, customer_id: str = None, order_id: str = None, product_id: str = None) -> dict:
#     """
#     Call the billingExtension API to extend the billing period.

#     Required parameters:
#         extension_days (str): Number of days for the extension.
#         phone (str): Customer's phone number.

#     Optional parameters:
#         customer_id (str): Customer identifier.
#         order_id (str): Order identifier.
#         product_id (str): Product identifier.

#     Returns:
#         dict: The JSON response from the billingExtension API.

#     Raises:
#         requests.RequestException: If the request fails.
#     """
#     formatted_phone = phone.lstrip("+")  # Remove '+' if present

#     BASE_URL = os.getenv("BACKEND_BASE_URL", "https://legalaibots-backend-vy7ua.ondigitalocean.app")
#     url = f"{BASE_URL}/api/voice-bot/billingExtension"
    
#     # Build payload with required parameters only.
#     payload = {
#         "extension_days": extension_days,
#         "phone": formatted_phone,
#     }
#     # Include optional parameters if provided.
#     if customer_id:
#         payload["customer_id"] = customer_id
#     if order_id:
#         payload["order_id"] = order_id
#     if product_id:
#         payload["product_id"] = product_id

#     try:
#         response = requests.post(url, json=payload, timeout=10)
#         response.raise_for_status()  # Raise an exception for HTTP errors.
#         return response.json()
#     except requests.RequestException as e:
#         # In production, you might want to log this error.
#         print(f"Error calling billingExtension API: {e}")
#         raise

async def billing_extension(extension_days: str, phone: str, customer_id: str = None, order_id: str = None, product_id: str = None) -> dict:
    formatted_phone = phone.lstrip("+")  # Remove '+' if present
    BASE_URL = os.getenv("BACKEND_BASE_URL", "https://legalaibots-backend-vy7ua.ondigitalocean.app")
    url = f"{BASE_URL}/api/voice-bot/billingExtension"
    
    payload = {
        "extension_days": extension_days,
        "phone": formatted_phone,
    }
    if customer_id:
        payload["customer_id"] = customer_id
    if order_id:
        payload["order_id"] = order_id
    if product_id:
        payload["product_id"] = product_id

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=10) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"Error calling billingExtension API: {e}")
            raise


# def cancel_order(
#     flag: str,
#     phone: str,
#     legalOrderId: str = None,
#     upsellOrderId: str = None,
#     legalOrderSubscriptionId: str = None,
#     upsellOrderSubscriptionId: str = None,
#     customer_id: str = None,
#     cancellation_reason: str = None
# ) -> dict:
#     """
#     Call the cancelOrder API to cancel an order.

#     Required Parameters:
#         flag (str): Cancellation flag. Valid values: "upsell", "legal", "both", or "legal&upsell".
#         phone (str): Customer phone number.

#     Optional Parameters:
#         legalOrderId (str): Legal order identifier.
#         upsellOrderId (str): Upsell order identifier.
#         legalOrderSubscriptionId (str): Legal order subscription identifier.
#         upsellOrderSubscriptionId (str): Upsell order subscription identifier.
#         customer_id (str): Customer identifier.
#         cancellation_reason (str): Reason for cancellation.

#     Returns:
#         dict: The JSON response from the cancelOrder API.

#     Raises:
#         requests.RequestException: If the request fails.
#     """
#     BASE_URL = os.getenv("BACKEND_BASE_URL", "https://legalaibots-backend-vy7ua.ondigitalocean.app")
#     url = f"{BASE_URL}/api/voice-bot/cancelOrder"

#     formatted_phone = phone.lstrip("+") 

#     payload = {
#         "flag": flag,
#         "phone": formatted_phone
#     }
#     if legalOrderId:
#         payload["legalOrderId"] = legalOrderId
#     if upsellOrderId:
#         payload["upsellOrderId"] = upsellOrderId
#     if legalOrderSubscriptionId:
#         payload["legalOrderSubscriptionId"] = legalOrderSubscriptionId
#     if upsellOrderSubscriptionId:
#         payload["upsellOrderSubscriptionId"] = upsellOrderSubscriptionId
#     if customer_id:
#         payload["customer_id"] = customer_id
#     if cancellation_reason:
#         payload["cancellation_reason"] = cancellation_reason

#     try:
#         response = requests.post(url, json=payload, timeout=10)
#         return response.json()
#     except requests.RequestException as e:
#         print(f"Error calling cancelOrder API: {e}")
#         raise

# UPDATED PART (replaced requests with aiohttp for async behavior):

import aiohttp  # <-- new import added for asynchronous HTTP calls

async def cancel_order(
    flag: str,
    phone: str,
    legalOrderId: str = None,
    upsellOrderId: str = None,
    legalOrderSubscriptionId: str = None,
    upsellOrderSubscriptionId: str = None,
    customer_id: str = None,
    cancellation_reason: str = None
) -> dict:
    BASE_URL = os.getenv("BACKEND_BASE_URL", "https://legalaibots-backend-vy7ua.ondigitalocean.app")
    url = f"{BASE_URL}/api/voice-bot/cancelOrder"

    formatted_phone = phone.lstrip("+") 

    payload = {
        "flag": flag,
        "phone": formatted_phone
    }
    if legalOrderId:
        payload["legalOrderId"] = legalOrderId
    if upsellOrderId:
        payload["upsellOrderId"] = upsellOrderId
    if legalOrderSubscriptionId:
        payload["legalOrderSubscriptionId"] = legalOrderSubscriptionId
    if upsellOrderSubscriptionId:
        payload["upsellOrderSubscriptionId"] = upsellOrderSubscriptionId
    if customer_id:
        payload["customer_id"] = customer_id
    if cancellation_reason:
        payload["cancellation_reason"] = cancellation_reason

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=payload, timeout=10) as response:
                return await response.json()
        except aiohttp.ClientError as e:
            print(f"Error calling cancelOrder API: {e}")
            raise

# data = billing_extension(extension_days='13', phone='+923364589301')
# print(type(data))

# data = get_customer_data("+923456710033")
# print(data)
# data = cancel_order(flag = 'legal', phone = '+923364589301')
# print(data)
# data['']
# print(data['response']['customer_legal_status'])
# import asyncio

# async def main():
#     data = await billing_extension(extension_days='1', phone = '+923114663661')
#     # removed_value = data['response'].pop('legal_order_history', None)
#     # removed_value1 = data['response'].pop('upsell_order_history', None)
#     print("Customer data:", data)

# if __name__ == "__main__":
#     asyncio.run(main())