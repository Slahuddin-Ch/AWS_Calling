tools = [
            {
                "type": "function",
                "name": "get_user_data",
                "description": "Get the user information from the Database...",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone_number": { "type": "string", "description": "It is 11 digit phone number of user starting with country code" }
                    },
                    "required": ["phone_number"],

                }
            }
        ]