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
            # {
            #     "type": "function",
            #     "name": "end_call",
            #     "description": "End the ongoing call",
            #     "parameters": {
            #         "type": "object",
            #         "properties": {
            #             "callSid": { "type": "string", "description": "It is unique Id of the call." }
            #         },
            #         "required": ["callSid"],

            #     }
            # },
            # {
            #     "type": "function",
            #     "name": "forward_call",
            #     "description": "forward the ongoing call",
            #     "parameters": {
            #         "type": "object",
            #         "properties": {
            #             "callSid": { "type": "string", "description": "It is unique Id of the call." }
            #         },
            #         "required": ["callSid"],

            #     }
            # },
            {
                "type": "function",
                "name": "cancel_order",
                "description": "Cancel an order.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone_number": { "type": "string", "description": "The registered phone number of the user." },
                        "subscription_name": { "type": "string", "description": "The name of the order the user wants to cancel.", "enum": ["legal", "upsell", "legal&upsell", "both"] }
                    },
                    "required": ["phone_number", "subscription_name"]
                }
            },
            {
                "type": "function",
                "name": "trial_extension",
                "description": "Extend a user's trial period.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "phone_number": { "type": "string", "description": "The registered phone number of the user." }
                    },
                    "required": ["phone_number"]
                }
            },
            {
                "type": "function",
                "name": "request_attorney_list",
                "description": "Retrieve a list of attorneys.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": { "type": "string", "description": "The name of the user." },
                        "city": { "type": "string", "description": "The city where the user wants to find attorneys." },
                        "state": { "type": "string", "description": "The state where the user wants to find attorneys." }
                    },
                    "required": ["name", "city", "state"]
                }
            },
        ]