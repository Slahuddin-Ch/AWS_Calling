tools = [
            {
                "type": "function",
                "name": "get_user_data",
                "description": "Get the user information from the Database...",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone_number": { "type": "string", "description": "It is phone number of user that consists of country code plus 10 digits, e.g., country code like `+92` and `1` etc and 10 digits like `3332326709`" }
                    },
                    "required": ["phone_number"],

                }
            },
        ]