import os
import json
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import Tool, StructuredTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from pydantic import BaseModel, Field
from api.tools.rag_tool import chipchip_rag_tool
from api.tools import database_tool


def create_kcart_agent(user=None):
    """
    Creates a LangChain agent with tools and prompts based on user authentication and role.
    Returns an AgentExecutor configured for the KcartBot application.
    """
    
    # Initialize tools and prompt instructions
    available_tools = []
    prompt_instructions = []
    
    # ============ CONCIERGE BLOCK (Available to all users) ============
    base_instruction = """You are KcartBot, an AI assistant for ChipChip, an Ethiopian agricultural marketplace.

STRICT SCOPE LIMITATIONS - You can ONLY help with:
1. ChipChip company information, services, and marketplace operations (use RAG tool ONLY for this)
2. Ethiopian agricultural products, farming, and food (use your general knowledge, NOT RAG)
3. Product storage, handling, and preservation tips (use your general knowledge, NOT RAG)
4. Nutritional information about agricultural products (use your general knowledge, NOT RAG)
5. Ethiopian recipes using local agricultural products (use your general knowledge, NOT RAG)
6. Agricultural marketplace transactions and processes

RAG TOOL USAGE:
- ONLY use the RAG tool for ChipChip company-specific questions
- DO NOT use RAG for general agricultural questions, storage tips, recipes, or farming advice
- Use your general LLM knowledge for agricultural topics

FORBIDDEN TOPICS - You MUST refuse to answer questions about:
- Sports, entertainment, politics, or current events
- Technology outside of agricultural applications
- Personal advice unrelated to agriculture
- Any topic not related to Ethiopian agriculture, food, or ChipChip marketplace
- General knowledge questions outside your agricultural scope

RESPONSE GUIDELINES:
- If asked about forbidden topics, politely say: "I'm KcartBot, specialized in Ethiopian agriculture and the ChipChip marketplace. I can only help with agricultural products, farming, food, and marketplace questions. How can I assist you with those topics?"
- Always stay focused on your agricultural and marketplace expertise
- Be helpful, friendly, and culturally aware within your scope only

When you receive retrieved documents from the RAG tool, use only the relevant ones to answer the query.

CURRENT DATE AND TIME:
Today's date is {current_date}. Use this as reference when users mention relative dates like "today", "tomorrow", or "in X days"."""
    
    # Get current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    base_instruction = base_instruction.format(current_date=current_date)
    
    prompt_instructions.append(base_instruction)
    
    # Add RAG tool (available to everyone) - ONLY for ChipChip company information
    rag_tool = Tool(
        name="chipchip_knowledge_search",
        func=chipchip_rag_tool,
        description="""Search ChipChip's knowledge base for information about:
        - Company policies, services, and features
        - ChipChip company information only
        - chipchip Marketplace operations and procedures
        DO NOT use this for general agricultural questions, storage tips, or recipes.
        Input should be a search query string. The tool will return the top 3 relevant documents."""
    )
    available_tools.append(rag_tool)
    
    # ============ AUTHENTICATION BLOCK ============
    if user and user.is_authenticated:
        # ============ ROLE-SPECIFIC TOOLS AND INSTRUCTIONS ============
        
        if user.role == 'customer':
            # Define input schemas using Pydantic
            class FindProductsInput(BaseModel):
                product_name: str = Field(description="Name of the product to search for")
                quantity: float = Field(description="Quantity needed")
            
            class CreateOrderInput(BaseModel):
                items: str = Field(description="JSON string of items list. Each item must have product_name (MUST BE IN ENGLISH - use 'Avocados' not 'አቮካዶ'), quantity, and supplier_id. Example: '[{\"product_name\": \"Avocados\", \"quantity\": 50, \"supplier_id\": \"uuid\"}]'")
                delivery_date: str = Field(description="Delivery date in YYYY-MM-DD format")
                delivery_location: str = Field(description="Delivery location/address")
            
            # Customer-specific tools
            def find_products_wrapper(product_name: str, quantity: float) -> str:
                """Searches for products and available suppliers."""
                try:
                    result = database_tool.find_product_listings(user, product_name, quantity)
                    return json.dumps(result, indent=2)
                except Exception as e:
                    return json.dumps({'error': str(e)})
            
            def create_order_wrapper(items: str, delivery_date: str, delivery_location: str) -> str:
                """Creates a new order for the customer."""
                try:
                    # Parse items from JSON string to list
                    items_list = json.loads(items) if isinstance(items, str) else items
                    result = database_tool.create_order_in_db(user, items_list, delivery_date, delivery_location)
                    return json.dumps(result, indent=2)
                except Exception as e:
                    return json.dumps({'error': str(e)})
            
            find_products_tool = StructuredTool.from_function(
                func=find_products_wrapper,
                name="find_product_listings",
                description="Searches for products and available suppliers. Returns list of suppliers with prices and availability.",
                args_schema=FindProductsInput
            )
            
            create_order_tool = StructuredTool.from_function(
                func=create_order_wrapper,
                name="create_order",
                description="Creates a new order for the customer with specified items, delivery date, and location.",
                args_schema=CreateOrderInput
            )
            
            available_tools.extend([find_products_tool, create_order_tool])
            
            customer_instruction = """
You are assisting a CUSTOMER. You can help them:
- Search for products and compare supplier prices using the find_product_listings tool
- Place orders with specific suppliers using the create_order tool
- Get information about products and pricing
- Answer questions about the ordering process

When helping customers:
1. Always confirm product details and quantities before searching
2. Present supplier options clearly with prices, showing BOTH supplier_name AND supplier_id
3. IMPORTANT: When customers want to order, ask them to choose by SUPPLIER ID (not name) to avoid confusion
4. CRITICAL: Always use ENGLISH product names in the create_order tool (e.g., "Avocados" not "አቮካዶ")
5. Always use supplier_id in the create_order tool, never supplier names
6. Confirm order details before creating an order
7. Be helpful in explaining the marketplace process

DISPLAYING PRODUCT LISTINGS:
- Format: "**[supplier_name]** (Supplier ID: `[supplier_id]`): [price] ETB"
- Do NOT include image_url in the customer-facing response
- Images are only for supplier's internal use, not shown to customers

SUPPLIER SELECTION PROCESS:
- Show supplier options with both name and ID
- Ask customer to choose by supplier_id
- Use supplier_id in order creation to ensure accuracy
"""
            prompt_instructions.append(customer_instruction)
            
        elif user.role == 'supplier':
            # Define input schemas using Pydantic
            class ProductNameInput(BaseModel):
                product_name: str = Field(description="Name of the product")
            
            class PricingSuggestionInput(BaseModel):
                product_name: str = Field(description="Name of the product")
                days: int = Field(default=30, description="Number of days of history to analyze")
            
            class InventoryInput(BaseModel):
                product_name: str = Field(description="Name of the product")
                quantity: float = Field(description="Quantity available")
                price: float = Field(description="Price per unit in ETB")
                available_date: str = Field(description="Date when product is available (YYYY-MM-DD)")
                expiry_date: str = Field(default=None, description="Optional expiry date (YYYY-MM-DD)")
                image_url: str = Field(default='', description="Optional image URL for the product (get from generate_product_image tool)")
            
            class UpdateOrderInput(BaseModel):
                order_id: str = Field(description="Order ID to update")
                new_status: str = Field(description="New status: 'accepted' or 'declined'")
                decline_reason: str = Field(default='', description="Optional reason for declining the order (only used when status is 'declined')")
            
            class ImageGenerationInput(BaseModel):
                product_description: str = Field(description="Detailed description of the product image to generate. Be specific about appearance, setting, and quality.")
            
            # Supplier-specific tools
            def check_inventory_wrapper(product_name: str) -> str:
                """Check if you have existing inventory for a product."""
                try:
                    result = database_tool.check_existing_inventory(user, product_name)
                    return json.dumps(result if result else {'message': 'No inventory found'}, indent=2)
                except Exception as e:
                    return json.dumps({'error': str(e)})
            
            def get_pricing_wrapper(product_name: str, days: int = 30) -> str:
                """Get market pricing suggestions based on competitor data."""
                try:
                    result = database_tool.get_comprehensive_pricing_suggestion(user, product_name, days)
                    return json.dumps(result, indent=2)
                except Exception as e:
                    return json.dumps({'error': str(e)})
            
            def add_update_inventory_wrapper(product_name: str, quantity: float, price: float, 
                                            available_date: str, expiry_date: str = None, image_url: str = '') -> str:
                """Add new inventory or update existing inventory with optional image."""
                try:
                    params = {
                        'product_name': product_name,
                        'quantity': quantity,
                        'price': price,
                        'available_date': available_date,
                        'expiry_date': expiry_date
                    }
                    # Add image_url if provided
                    if image_url:
                        params['image_url'] = image_url
                    
                    result = database_tool.add_or_update_inventory(user, params)
                    return json.dumps(result, indent=2)
                except Exception as e:
                    return json.dumps({'error': str(e)})
            
            def get_inventory_wrapper(query: str = "") -> str:
                """Get all your active inventory listings."""
                try:
                    result = database_tool.get_supplier_inventory(user)
                    return json.dumps(result, indent=2)
                except Exception as e:
                    return json.dumps({'error': str(e)})
            
            def get_orders_wrapper(status_filter: str = '', date_filter: str = '') -> str:
                """Get orders that include your products. Filter by status (accepted, pending_acceptance, declined, completed) or date (today, yesterday, YYYY-MM-DD)."""
                try:
                    # Convert empty strings to None
                    status = status_filter if status_filter else None
                    date = date_filter if date_filter else None
                    result = database_tool.get_supplier_orders(user, status_filter=status, date_filter=date)
                    return json.dumps(result, indent=2)
                except Exception as e:
                    return json.dumps({'error': str(e)})
            
            def update_order_wrapper(order_id: str, new_status: str, decline_reason: str = '') -> str:
                """Accept or decline an order. Provide decline_reason when declining."""
                try:
                    result = database_tool.update_order_status(user, order_id, new_status, decline_reason)
                    return json.dumps(result, indent=2)
                except Exception as e:
                    return json.dumps({'error': str(e)})
            
            def generate_image_wrapper(product_description: str) -> str:
                """Generate a product image based on description."""
                try:
                    from api.utils.image_generator import generate_product_image_sync
                    image_url = generate_product_image_sync(product_description)
                    return json.dumps({
                        'success': True,
                        'image_url': image_url,
                        'message': 'Image generated successfully. Please review and confirm if you like it.'
                    }, indent=2)
                except Exception as e:
                    return json.dumps({'error': str(e)})
            
            check_inventory_tool = StructuredTool.from_function(
                func=check_inventory_wrapper,
                name="check_existing_inventory",
                description="Check if you have existing inventory for a product.",
                args_schema=ProductNameInput
            )
            
            pricing_tool = StructuredTool.from_function(
                func=get_pricing_wrapper,
                name="get_pricing_suggestion",
                description="Get market pricing suggestions for a product based on competitor data and sales history.",
                args_schema=PricingSuggestionInput
            )
            
            add_inventory_tool = StructuredTool.from_function(
                func=add_update_inventory_wrapper,
                name="add_or_update_inventory",
                description="Add new inventory or update existing inventory with product details and pricing.",
                args_schema=InventoryInput
            )
            
            # Define input schemas for no-argument tools
            class EmptyInput(BaseModel):
                """Schema for tools that don't require any input."""
                pass
            
            # StructuredTool for getting inventory
            get_inventory_tool = StructuredTool.from_function(
                func=lambda: get_inventory_wrapper(""),
                name="get_my_inventory",
                description="Get all your active inventory listings with expiring items alerts.",
                args_schema=EmptyInput
            )
            
            # Input schema for getting orders
            class GetOrdersInput(BaseModel):
                """Schema for filtering orders."""
                status_filter: str = Field(default='', description="Optional filter by status: 'accepted', 'pending_acceptance', 'declined', 'completed', 'out_for_delivery'. Leave empty for all statuses.")
                date_filter: str = Field(default='', description="Optional filter by date: 'today', 'yesterday', or specific date 'YYYY-MM-DD'. Leave empty for all dates.")
            
            # StructuredTool for getting orders
            get_orders_tool = StructuredTool.from_function(
                func=get_orders_wrapper,
                name="get_my_orders",
                description="Get orders that include your products. Can filter by status (accepted, pending_acceptance, etc.) or date (today, yesterday, specific date).",
                args_schema=GetOrdersInput
            )
            
            update_order_tool = StructuredTool.from_function(
                func=update_order_wrapper,
                name="update_order_status",
                description="Accept or decline a customer order.",
                args_schema=UpdateOrderInput
            )
            
            image_generation_tool = StructuredTool.from_function(
                func=generate_image_wrapper,
                name="generate_product_image",
                description="Generate a product image based on description. Returns an image URL that can be used when adding inventory.",
                args_schema=ImageGenerationInput
            )
            
            available_tools.extend([
                check_inventory_tool,
                pricing_tool,
                add_inventory_tool,
                get_inventory_tool,
                get_orders_tool,
                update_order_tool,
                image_generation_tool
            ])
            
            supplier_instruction = """
You are assisting a SUPPLIER on ChipChip marketplace. Be friendly and helpful!

BASIC INTERACTIONS:
- When greeted, warmly welcome them and explain you can help with inventory management, pricing, and orders
- Always be professional and supportive
- Understand natural language requests

YOU CAN HELP SUPPLIERS WITH:
- Check specific product availability: use check_existing_inventory tool
- Get market pricing suggestions: use get_pricing_suggestion tool
- Add or update inventory listings: use add_or_update_inventory tool
- View ALL their inventory/stock: use get_my_inventory tool
- View orders they received: use get_my_orders tool
- Accept or decline orders: use update_order_status tool

IMPORTANT - WHEN TO USE EACH TOOL:
- "check my stock" OR "check my inventory" OR "show my inventory" = use get_my_inventory
- "check if I have [product]" OR "do I have [product]" = use check_existing_inventory
- "show my orders" OR "what orders do I have" = use get_my_orders with appropriate filters:
  * "show my accepted orders" = get_my_orders(status_filter='accepted')
  * "show today's orders" = get_my_orders(date_filter='today')
  * "show accepted orders from today" = get_my_orders(status_filter='accepted', date_filter='today')
  * "show pending orders" = get_my_orders(status_filter='pending_acceptance')
  * No filters = shows all orders grouped by status

CRITICAL: When a supplier asks to see their inventory/stock (use get_my_inventory):
1. The tool returns a dictionary with: inventory list, expiring_soon list, and has_expiring_items flag
2. If has_expiring_items is TRUE, you MUST:
   a) FIRST alert them about items expiring within 5 days
   b) Show which products are expiring and when (days_until_expiry)
   c) Suggest they reduce prices to sell before expiration
   d) Ask if they want to reduce the price for these expiring items
3. THEN show their full inventory list

IMPORTANT: When a supplier wants to add or update inventory:
1. For NEW inventory: ALWAYS use get_pricing_suggestion FIRST to get market data
2. Present the pricing suggestions with ALL details in this format:
   - "Based on market data for the last 30 days, here are pricing suggestions for [product]:"
   - "**Suggested price range:** X - Y ETB per unit"
   - "**Highest volume price (last 30 days):** Z ETB per unit"
   - "**Competitor averages:**"
   - "  - Distribution centers: XX ETB per unit"
   - "  - Local shops: XX ETB per unit"
   - "  - Supermarkets: XX ETB per unit"
3. For UPDATES: Use the actual English product name from the database (e.g., "butter" not "ቅቤ")
4. When a supplier refers to a product they just viewed, extract the English product name from your previous response

HANDLING DATES (CRITICAL):
- If user says "today" or "now", use today's date in YYYY-MM-DD format
- If user says "tomorrow", use tomorrow's date
- If user says "after X days", "in X days", or "X days from now", calculate the date X days from today
- If user provides relative dates (like "expires in 4 days" or "expired after 4 days"), calculate the absolute date
- Always convert relative dates to absolute YYYY-MM-DD format before calling tools
- Today's date is provided in your system context

HANDLING USER INPUT FOR INVENTORY:
- Users may provide all information in one message (quantity, price, dates)
- Extract all relevant information from their message:
  * Quantity and unit (e.g., "50 liters", "30 kg")
  * Price (e.g., "30 birr", "40 ETB")
  * Available date (parse relative dates like "today", "tomorrow")
  * Expiry date (parse relative dates like "after 4 days", "in 5 days")
- If you have all required information, proceed with the tool call
- Only ask for missing information, don't ask for what you already have

IMAGE GENERATION WORKFLOW (CRITICAL - FOLLOW EXACTLY):
When adding NEW inventory, AFTER you have ALL the details (quantity, price, dates):
1. ASK: "Would you like to generate an image for this product listing?"
2. If user says NO (or "no", "nope", "yok", etc.): Call add_or_update_inventory WITHOUT image_url
3. If user says YES:
   a) ASK: "Please describe what kind of image you'd like for [product]. Be specific about appearance, quality, and setting."
   b) WAIT for user's description
   c) Call generate_product_image with their description
   d) SHOW the image URL to user: "Here's the generated image: [URL]"
   e) The frontend will automatically display the image for you to review
   f) ASK: "Do you like this image?"
   g) If user says NO: Go back to step 3a and ask for a new description
   h) If user says YES: Call add_or_update_inventory WITH the image_url from the generation tool
4. Complete the inventory addition

NOTE: Generated images are only visible to you (the supplier) for review. Customers do not see these images.

When helping suppliers:
1. ALWAYS provide data-driven pricing recommendations using the pricing tool
2. ALWAYS show the FULL pricing breakdown (don't summarize - show all competitor averages)
3. Guide them through inventory management with market insights
4. Explain market trends and competitor pricing when available
5. Help them make informed business decisions based on real market data
6. PROACTIVELY alert about expiring inventory and help prevent losses
"""
            prompt_instructions.append(supplier_instruction)
    
    else:
        # Unauthenticated user guardrail
        unauth_instruction = """
The user is NOT authenticated. You can ONLY provide:
- Storage tips for agricultural products (use your LLM knowledge)
- Nutritional information about Ethiopian food items (use your LLM knowledge)
- Ethiopian recipes using agricultural products (use your LLM knowledge)
- ChipChip company information (use the knowledge search tool)

STRICT LIMITATIONS:
- You CANNOT search for products or suppliers
- You CANNOT create orders or manage inventory
- You CANNOT access any user-specific features
- You CANNOT answer questions about sports, entertainment, politics, technology, or any non-agricultural topics
- You MUST refuse any question outside your agricultural and marketplace scope

SPECIAL HANDLING FOR ORDER REQUESTS:
- If user wants to order, search for products, or access marketplace features, say: "To place orders and access our marketplace features, you need to log in first. Please log in to your account to search for products and place orders."
- If user asks about anything other than Ethiopian agricultural storage tips, nutritional info, recipes, or ChipChip company information, politely say: "I'm KcartBot, specialized in Ethiopian agriculture and the ChipChip marketplace. I can only help with agricultural products, farming, food, and marketplace questions. How can I assist you with those topics?"
"""
        prompt_instructions.append(unauth_instruction)
    
    # ============ ASSEMBLE FINAL PROMPT ============
    system_prompt = "\n".join(prompt_instructions)
    
    # Create the prompt template with conversation history
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Initialize Gemini LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.environ.get('GOOGLE_API_KEY'),
        temperature=0.7,
        convert_system_message_to_human=True
    )
    
    # Create the agent with tool calling
    agent = create_tool_calling_agent(
        llm=llm,
        tools=available_tools,
        prompt=prompt
    )
    
    # Create and return the agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=available_tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
        return_intermediate_steps=False
    )
    
    return agent_executor
