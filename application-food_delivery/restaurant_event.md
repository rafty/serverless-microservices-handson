```mermaid
classDiagram
    
    RestaurantCreated_Restaurant *-- MenuItem_Restaurant
    RestaurantCreated_Kitchen *-- MenuItem_Kitchen
    RestaurantCreated_Order *-- MenuItem_Order
    
    class RestaurantCreated_Restaurant{
        restaurant_id
        restaurant_name
        restaurant_address
        menu_items
    }
    class MenuItem_Restaurant{
        menu_id
        menu_name
        price
    }
    
    class RestaurantCreated_Delivery{
        restaurant_id
        restaurant_name
        restaurant_address
    }
    
    class RestaurantCreated_Kitchen{
        restaurant_id
        menu_items
    }
    class MenuItem_Kitchen{
        menu_id
        menu_name
        price
    }
    
    class RestaurantCreated_Order{
        restaurant_id
        restaurant_name
        menu_items
    }
    class MenuItem_Order{
        menu_id
        menu_name
        price
    }


    


```