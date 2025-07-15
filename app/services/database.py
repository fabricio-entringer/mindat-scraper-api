"""
Database service for handling TinyDB operations.
"""

import logging
from typing import Dict, List, Optional, Any
from tinydb import TinyDB, Query
from tinydb.table import Document
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseService:
    """Database service for mineral data using TinyDB."""
    
    def __init__(self, db_path: str = "data/minerals.json"):
        """
        Initialize the database.
        
        Args:
            db_path: Path to the TinyDB database file
        """
        self.db_path = Path(db_path)
        # Create directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.db = TinyDB(self.db_path)
        self.minerals_table = self.db.table('minerals')
        logger.info(f"Database initialized at {self.db_path}")
    
    def save_mineral(self, mineral_data: Dict[str, Any]) -> bool:
        """
        Save mineral data to the database.
        
        Args:
            mineral_data: Dictionary containing mineral information
            
        Returns:
            True if successfully saved, False otherwise
        """
        try:
            # Use mineral_code as unique identifier
            mineral_code = mineral_data.get('mineral_code')
            if not mineral_code:
                logger.error("Mineral code is required")
                return False
            
            # Check if mineral already exists
            Mineral = Query()
            existing = self.minerals_table.search(Mineral.mineral_code == mineral_code)
            
            if existing:
                # Update existing record
                self.minerals_table.update(mineral_data, Mineral.mineral_code == mineral_code)
                logger.info(f"Updated mineral: {mineral_code}")
            else:
                # Insert new record
                self.minerals_table.insert(mineral_data)
                logger.info(f"Saved new mineral: {mineral_code}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving mineral data: {str(e)}")
            return False
    
    def get_mineral(self, mineral_code: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve mineral data by code.
        
        Args:
            mineral_code: Unique identifier for the mineral
            
        Returns:
            Dictionary containing mineral data or None if not found
        """
        try:
            Mineral = Query()
            result = self.minerals_table.search(Mineral.mineral_code == mineral_code)
            
            if result:
                return result[0]
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving mineral {mineral_code}: {str(e)}")
            return None
    
    def get_all_minerals(self) -> List[Dict[str, Any]]:
        """
        Retrieve all minerals from the database.
        
        Returns:
            List of all mineral records
        """
        try:
            return self.minerals_table.all()
        except Exception as e:
            logger.error(f"Error retrieving all minerals: {str(e)}")
            return []
    
    def delete_mineral(self, mineral_code: str) -> bool:
        """
        Delete mineral by code.
        
        Args:
            mineral_code: Unique identifier for the mineral
            
        Returns:
            True if successfully deleted, False otherwise
        """
        try:
            Mineral = Query()
            result = self.minerals_table.remove(Mineral.mineral_code == mineral_code)
            
            if result:
                logger.info(f"Deleted mineral: {mineral_code}")
                return True
            else:
                logger.warning(f"Mineral not found: {mineral_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting mineral {mineral_code}: {str(e)}")
            return False
    
    def search_minerals(self, query: str) -> List[Dict[str, Any]]:
        """
        Search minerals by name or description.
        
        Args:
            query: Search query string
            
        Returns:
            List of matching mineral records
        """
        try:
            Mineral = Query()
            results = self.minerals_table.search(
                (Mineral.name.test(lambda x: query.lower() in x.lower() if x else False)) |
                (Mineral.description.test(lambda x: query.lower() in x.lower() if x else False))
            )
            return results
        except Exception as e:
            logger.error(f"Error searching minerals: {str(e)}")
            return []
    
    def search_minerals_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Search minerals by exact name match.
        
        Args:
            name: Name to search for (exact match, case-insensitive)
            
        Returns:
            List of matching mineral records
        """
        try:
            Mineral = Query()
            
            # Exact match search (case-insensitive)
            results = self.minerals_table.search(
                Mineral.name.test(lambda x: x.lower() == name.lower() if x else False)
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching minerals by name: {str(e)}")
            return []
    
    def search_minerals_by_partial_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Search minerals by partial name match for API convenience.
        
        Args:
            name: Name to search for (partial match, case-insensitive)
            
        Returns:
            List of matching mineral records sorted by relevance
        """
        try:
            Mineral = Query()
            
            # Partial match search (case-insensitive)
            results = self.minerals_table.search(
                Mineral.name.test(lambda x: name.lower() in x.lower() if x else False)
            )
            
            # Sort results by name similarity (exact matches first, then partial matches)
            def similarity_score(mineral):
                mineral_name = mineral.get('name', '').lower()
                search_name = name.lower()
                
                if mineral_name == search_name:
                    return 0  # Exact match
                elif mineral_name.startswith(search_name):
                    return 1  # Starts with search term
                elif search_name in mineral_name:
                    return 2  # Contains search term
                else:
                    return 3  # Other matches
            
            results.sort(key=similarity_score)
            return results
            
        except Exception as e:
            logger.error(f"Error searching minerals by partial name: {str(e)}")
            return []
    
    def get_mineral_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get mineral by exact name match.
        
        Args:
            name: Exact name of the mineral
            
        Returns:
            Dictionary containing mineral data or None if not found
        """
        try:
            Mineral = Query()
            result = self.minerals_table.search(
                Mineral.name.test(lambda x: x.lower() == name.lower() if x else False)
            )
            
            if result:
                return result[0]  # Return first exact match
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving mineral by name {name}: {str(e)}")
            return None
    
    def close(self):
        """Close the database connection."""
        self.db.close()
        logger.info("Database connection closed")
