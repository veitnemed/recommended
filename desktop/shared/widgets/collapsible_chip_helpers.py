"""Shared expand/collapse behavior for chip filter selectors."""

from __future__ import annotations

from PyQt6.QtWidgets import QPushButton

COLLAPSED_VISIBLE_CHIP_COUNT = 5


class ChipExpandControl:
    """Show the first N chips; expand to reveal the rest on demand."""

    def __init__(
        self,
        *,
        visible_count: int = COLLAPSED_VISIBLE_CHIP_COUNT,
        expand_object_name: str = "chipExpandToggle",
    ) -> None:
        self.visible_count = visible_count
        self.expanded = False
        self._expand_object_name = expand_object_name
        self._button: QPushButton | None = None
        self._total = 0

    def create_button(self) -> QPushButton:
        button = QPushButton()
        button.setObjectName(self._expand_object_name)
        button.setFlat(True)
        self._button = button
        return button

    def reset(self) -> None:
        self.expanded = False

    def toggle(self) -> None:
        self.expanded = not self.expanded

    def apply_visibility(self, chips: list[QPushButton]) -> None:
        self._total = len(chips)
        if not self.expanded:
            for index, chip in enumerate(chips):
                if index >= self.visible_count and chip.isChecked():
                    self.expanded = True
                    break

        for index, chip in enumerate(chips):
            chip.setVisible(self.expanded or index < self.visible_count)

        self._update_button()

    def _update_button(self) -> None:
        if self._button is None:
            return
        hidden_count = max(0, self._total - self.visible_count)
        self._button.setVisible(hidden_count > 0)
        if hidden_count <= 0:
            return
        if self.expanded:
            self._button.setText("Свернуть ▲")
        else:
            self._button.setText(f"Показать ещё ({hidden_count}) ▼")
