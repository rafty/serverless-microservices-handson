from __future__ import annotations  # classの依存関係の許可
from restaurant_layers.domain import restaurant_model
from restaurant_layers.service import commands
from restaurant_layers.common import exception


class RestaurantService:

    def __init__(self, restaurant_repo, restaurant_event_repo):
        self.restaurant_repo = restaurant_repo
        self.restaurant_event_repo = restaurant_event_repo

    def create_restaurant(self, cmd: commands.CreateRestaurant) -> int:
        # restaurant_idの作成する
        new_restaurant_id = self.restaurant_repo.get_unique_restaurant_id()
        restaurant, domain_events = restaurant_model.Restaurant.create(new_restaurant_id,
                                                                       cmd.restaurant_name,
                                                                       cmd.restaurant_address,
                                                                       cmd.menu_items)
        self.restaurant_repo.save(restaurant)
        self.restaurant_event_repo.save(domain_events)

        # return {'restaurant_id': restaurant.restaurant_id}
        return commands.CreateRestaurantResponse.from_obj(restaurant)

    def find_by_id(self, cmd: commands.GetRestaurant) -> restaurant_model.Restaurant:
        restaurant = self.restaurant_repo.find_by_id(cmd.restaurant_id)
        if restaurant is None:
            raise exception.InvalidName(f'Invalid name {cmd.restaurant_id}')
        return restaurant
        # Todo: ResponseのClassを作成する

