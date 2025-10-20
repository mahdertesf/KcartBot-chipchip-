import os
import asyncio
from runware import Runware, IImageInference


async def generate_product_image(product_description: str) -> str:
    """
    Generates a product image using Runware API based on the description.
    
    Args:
        product_description: Description of the image to generate
        
    Returns:
        str: URL of the generated image
        
    Raises:
        Exception: If image generation fails
    """
    try:
        runware_api_key = os.environ.get('RUNWARE_API_KEY')
        
        if not runware_api_key:
            raise ValueError("RUNWARE_API_KEY not found in environment variables")
        
        runware = Runware(api_key=runware_api_key)
        
        # Establish connection
        await runware.connect()
        
        # Create image generation request
        request = IImageInference(
            positivePrompt=f"{product_description}, professional product photography, high quality, well lit, market display",
            model="runware:101@1",
            width=1024,
            height=1024
        )
        
        # Generate image
        images = await runware.imageInference(requestImage=request)
        
        # Get the first image URL
        image_url = images[0].imageURL if images else None
        
        # Disconnect
        await runware.disconnect()
        
        if not image_url:
            raise Exception("No image was generated")
        
        return image_url
        
    except Exception as e:
        print(f"Error generating image: {e}")
        raise


def generate_product_image_sync(product_description: str) -> str:
    """
    Synchronous wrapper for generate_product_image.
    
    Args:
        product_description: Description of the image to generate
        
    Returns:
        str: URL of the generated image
    """
    try:
        # Create new event loop if needed
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async function
        image_url = loop.run_until_complete(generate_product_image(product_description))
        return image_url
        
    except Exception as e:
        raise Exception(f"Image generation failed: {str(e)}")

