from notion_client import Client
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_notion_connection():
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    notion_api_key = os.getenv('NOTION_API_KEY')
    database_id = os.getenv('NOTION_DATABASE_ID')
    
    if not notion_api_key or not database_id:
        logger.error("❌ Missing required environment variables")
        logger.error("Please ensure NOTION_API_KEY and NOTION_DATABASE_ID are set in .env")
        return False
    
    try:
        # Initialize Notion client
        notion = Client(auth=notion_api_key)
        
        # Format database ID (add hyphens if needed)
        formatted_db_id = database_id
        if len(database_id) == 32:
            formatted_db_id = f"{database_id[:8]}-{database_id[8:12]}-{database_id[12:16]}-{database_id[16:20]}-{database_id[20:]}"
        
        # Try to retrieve database
        db = notion.databases.retrieve(formatted_db_id)
        
        # Extract database details
        db_name = db["title"][0]["plain_text"] if db["title"] else "Unnamed Database"
        db_properties = list(db["properties"].keys())
        
        # Print success information
        logger.info("✅ Successfully connected to Notion database")
        logger.info(f"Database Name: {db_name}")
        logger.info(f"Available Properties: {', '.join(db_properties)}")
        
        # Test query capability
        query_result = notion.databases.query(formatted_db_id, page_size=1)
        logger.info(f"Query test successful. Database contains {len(query_result['results'])} or more entries.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error connecting to Notion database: {str(e)}")
        logger.error("Please check your API key and database ID")
        logger.error("Make sure the integration has access to the database")
        return False

if __name__ == "__main__":
    test_notion_connection()