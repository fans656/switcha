import math
from typing import Callable

from switcha import utils


class Slots(list):

    def __init__(
            self,
            get_items: Callable[[], list[any]],
            *,
            min_n_rows=2,
            n_cols=4,
    ):
        self.get_items = get_items
        self.min_n_rows = min_n_rows
        self.n_cols = 4
        
        self.update()
    
    @property
    def n_rows(self):
        return len(self) // self.n_cols
    
    def get_item(self, index):
        if 0 <= index < len(self):
            return self[index].item
    
    def index(self, item):
        return next((index for index, slot in enumerate(self) if slot.item == item), None)

    def swap(self, src_index, dst_index):
        n_slots = len(self)
        if 0 <= src_index < n_slots and 0 <= dst_index < n_slots:
            src_slot = self[src_index]
            dst_slot = self[dst_index]
            src_slot.item, dst_slot.item = dst_slot.item, src_slot.item
    
    def update(self):
        items = self.get_items()
        
        # ensure enough slots
        n_rows = max(math.ceil(len(items) / self.n_cols), self.min_n_rows)
        utils.resize(self, n_rows * self.n_cols, Slot)
        
        # remove disappeared items
        latest_items = set(items)
        for slot in self:
            if slot.item and slot.item not in latest_items:
                slot.item = None

        # add new items
        existed_items = {slot.item for slot in self if slot.item}
        available_slots = iter(slot for slot in self if slot.item is None)
        for item in items:
            if item not in existed_items:
                slot = next(available_slots)
                slot.item = item


class Slot:

    def __init__(self):
        self.item = None
