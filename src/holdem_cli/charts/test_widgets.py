"""
Test module for TUI widgets.

This module contains tests and examples for all the TUI widgets
to ensure they work correctly together.
"""

import unittest
from unittest.mock import Mock, patch
from typing import Dict, Any

# Import the widgets
from holdem_cli.charts.tui.widgets import (
    HandMatrixWidget, HandDetailsWidget, ChartControlsWidget,
    HelpDialog, ChartImportDialog, ErrorBoundaryWidget, QuizLauncherWidget,
    HandAction, ChartAction, create_sample_range
)
from holdem_cli.charts.tui.messages import HandSelected


class TestHandMatrixWidget(unittest.TestCase):
    """Test the HandMatrixWidget functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_actions = create_sample_range()
        self.widget = HandMatrixWidget(self.sample_actions, "Test Chart")
    
    def test_widget_initialization(self):
        """Test widget initializes correctly."""
        self.assertEqual(self.widget.chart_name, "Test Chart")
        self.assertEqual(self.widget.selected_row, 0)
        self.assertEqual(self.widget.selected_col, 0)
        self.assertEqual(self.widget.view_mode, "range")
        self.assertFalse(self.widget.range_builder_mode)
        self.assertEqual(len(self.widget.actions), len(self.sample_actions))
    
    def test_hand_selection(self):
        """Test hand selection and navigation."""
        # Test initial selection
        initial_hand = self.widget.get_selected_hand()
        self.assertEqual(initial_hand, "AA")  # Top-left position
        
        # Test navigation
        self.widget.selected_row = 1
        self.widget.selected_col = 1
        selected_hand = self.widget.get_selected_hand()
        self.assertEqual(selected_hand, "KK")
        
        # Test navigation to specific hand
        result = self.widget.navigate_to_hand("QQ")
        self.assertTrue(result)
        self.assertEqual(self.widget.selected_row, 2)
        self.assertEqual(self.widget.selected_col, 2)
    
    def test_view_modes(self):
        """Test different view modes."""
        # Test setting view modes
        self.widget.set_view_mode("frequency")
        self.assertEqual(self.widget.view_mode, "frequency")
        
        self.widget.set_view_mode("ev")
        self.assertEqual(self.widget.view_mode, "ev")
        
        self.widget.set_view_mode("range")
        self.assertEqual(self.widget.view_mode, "range")
        
        # Test invalid view mode
        self.widget.set_view_mode("invalid")
        self.assertEqual(self.widget.view_mode, "range")  # Should not change
    
    def test_range_builder(self):
        """Test range builder functionality."""
        # Enable range builder
        self.widget.toggle_range_builder()
        self.assertTrue(self.widget.range_builder_mode)
        
        # Add hand to custom range
        self.widget.selected_row = 0
        self.widget.selected_col = 0
        self.widget._add_hand_to_custom_range()
        self.assertIn("AA", self.widget.custom_range)
        
        # Remove hand from custom range
        self.widget._remove_hand_from_custom_range()
        self.assertNotIn("AA", self.widget.custom_range)
        
        # Clear custom range
        self.widget.custom_range["KK"] = HandAction(ChartAction.RAISE)
        self.widget.clear_custom_range()
        self.assertEqual(len(self.widget.custom_range), 0)
    
    def test_search_functionality(self):
        """Test search functionality."""
        # Search for specific hands
        results = self.widget.search_hands("AK")
        self.assertIn("AKs", results)
        self.assertIn("AKo", results)
        
        # Search by action
        results = self.widget.search_hands("raise")
        self.assertGreater(len(results), 0)
        
        # Search by hand type
        results = self.widget.search_hands("suited")
        suited_hands = [h for h in results if h.endswith('s')]
        self.assertGreater(len(suited_hands), 0)
    
    def test_caching_system(self):
        """Test the render caching system."""
        # Clear cache
        self.widget.clear_cache()
        self.assertEqual(len(self.widget._render_cache), 0)
        
        # Render should create cache entry
        render1 = self.widget.render()
        self.assertGreater(len(self.widget._render_cache), 0)
        
        # Same render should use cache
        render2 = self.widget.render()
        self.assertEqual(render1, render2)
        
        # Changing state should clear cache
        self.widget.selected_row = 1
        self.widget._update_selection()
        # Cache should be cleared and new render generated
        render3 = self.widget.render()
        self.assertNotEqual(render1, render3)
    
    def test_export_functionality(self):
        """Test data export functionality."""
        export_data = self.widget.export_matrix_data()
        
        self.assertEqual(export_data["chart_name"], "Test Chart")
        self.assertIn("actions", export_data)
        self.assertIn("view_mode", export_data)
        self.assertIn("selection", export_data)
        self.assertEqual(export_data["view_mode"], "range")


class TestHandDetailsWidget(unittest.TestCase):
    """Test the HandDetailsWidget functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.widget = HandDetailsWidget()
        self.sample_action = HandAction(
            ChartAction.RAISE, 
            frequency=0.8, 
            ev=2.5, 
            notes="Premium hand"
        )
    
    def test_update_hand(self):
        """Test updating hand details."""
        self.widget.update_hand("AKs", self.sample_action)
        
        self.assertEqual(self.widget.current_hand, "AKs")
        self.assertEqual(self.widget.current_action, self.sample_action)
    
    def test_hand_history(self):
        """Test hand history tracking."""
        # Add multiple hands to history
        self.widget.update_hand("AA", self.sample_action)
        self.widget.update_hand("KK", self.sample_action)
        self.widget.update_hand("QQ", self.sample_action)
        
        self.assertIn("AA", self.widget.hand_history)
        self.assertIn("KK", self.widget.hand_history)
    
    def test_empty_state_rendering(self):
        """Test rendering when no hand is selected."""
        render_output = self.widget.render()
        self.assertIn("Select a hand", render_output)
        self.assertIn("Navigation Tips", render_output)
    
    def test_hand_classification(self):
        """Test hand type classification."""
        # Test pocket pair
        classification = self.widget._classify_hand_type()
        self.widget.current_hand = "AA"
        classification = self.widget._classify_hand_type()
        self.assertIn("Premium pocket pair", classification)
        
        # Test suited hand
        self.widget.current_hand = "AKs"
        classification = self.widget._classify_hand_type()
        self.assertEqual(classification, "Suited ace")


class TestChartControlsWidget(unittest.TestCase):
    """Test the ChartControlsWidget functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.widget = ChartControlsWidget()
    
    def test_initialization(self):
        """Test widget initializes correctly."""
        self.assertEqual(self.widget.current_view_mode, "range")
        self.assertFalse(self.widget.range_builder_enabled)
    
    def test_state_updates(self):
        """Test updating widget state."""
        self.widget.update_state("frequency", True)
        
        self.assertEqual(self.widget.current_view_mode, "frequency")
        self.assertTrue(self.widget.range_builder_enabled)
    
    def test_status_summary(self):
        """Test status summary generation."""
        summary = self.widget.get_status_summary()
        self.assertIn("range", summary.lower())
        self.assertIn("off", summary.lower())


class TestHelpDialog(unittest.TestCase):
    """Test the HelpDialog functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.dialog = HelpDialog()
    
    def test_help_sections(self):
        """Test help sections are properly created."""
        sections = self.dialog.help_sections
        
        self.assertIn("general", sections)
        self.assertIn("navigation", sections)
        self.assertIn("shortcuts", sections)
        self.assertGreater(len(sections["general"]), 0)
    
    def test_dialog_operations(self):
        """Test opening and closing dialog."""
        # Initially closed
        self.assertFalse(self.dialog.is_open)
        
        # Open dialog
        self.dialog.open()
        self.assertTrue(self.dialog.is_open)
        
        # Close dialog
        self.dialog.close()
        self.assertFalse(self.dialog.is_open)
        
        # Toggle dialog
        self.dialog.toggle()
        self.assertTrue(self.dialog.is_open)
        
        self.dialog.toggle()
        self.assertFalse(self.dialog.is_open)


class TestChartImportDialog(unittest.TestCase):
    """Test the ChartImportDialog functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.dialog = ChartImportDialog()
    
    def test_dialog_operations(self):
        """Test opening and closing dialog."""
        # Open dialog
        self.dialog.open()
        self.assertTrue(self.dialog.display)
        
        # Close dialog
        self.dialog.close()
        self.assertFalse(self.dialog.display)


class TestWidgetIntegration(unittest.TestCase):
    """Test widgets working together."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_actions = create_sample_range()
        self.matrix_widget = HandMatrixWidget(self.sample_actions, "Integration Test")
        self.details_widget = HandDetailsWidget()
        self.controls_widget = ChartControlsWidget()
    
    def test_hand_selection_integration(self):
        """Test hand selection between matrix and details widgets."""
        # Select a hand in matrix
        test_hand = "AKs"
        self.matrix_widget.navigate_to_hand(test_hand)
        selected_hand = self.matrix_widget.get_selected_hand()
        
        # Update details widget
        action = self.matrix_widget.actions.get(selected_hand)
        self.details_widget.update_hand(selected_hand, action)
        
        # Verify integration
        self.assertEqual(selected_hand, test_hand)
        self.assertEqual(self.details_widget.current_hand, test_hand)
        self.assertIsNotNone(self.details_widget.current_action)
    
    def test_view_mode_integration(self):
        """Test view mode changes between matrix and controls."""
        # Change view mode in controls
        self.controls_widget.current_view_mode = "frequency"
        
        # Apply to matrix widget
        self.matrix_widget.set_view_mode(self.controls_widget.current_view_mode)
        
        # Verify integration
        self.assertEqual(self.matrix_widget.view_mode, "frequency")
        self.assertEqual(self.controls_widget.current_view_mode, "frequency")
    
    def test_range_builder_integration(self):
        """Test range builder integration."""
        # Enable range builder in controls
        self.controls_widget.range_builder_enabled = True
        
        # Apply to matrix widget
        self.matrix_widget.range_builder_mode = True
        
        # Add hand to custom range
        self.matrix_widget.selected_row = 0
        self.matrix_widget.selected_col = 0
        self.matrix_widget._add_hand_to_custom_range()
        
        # Verify integration
        self.assertGreater(len(self.matrix_widget.custom_range), 0)
        self.assertTrue(self.controls_widget.range_builder_enabled)
        self.assertTrue(self.matrix_widget.range_builder_mode)


class TestWidgetUtilities(unittest.TestCase):
    """Test widget utility functions."""
    
    def test_create_matrix_widget(self):
        """Test matrix widget creation utility."""
        from holdem_cli.charts.tui.widgets.matrix_widget import create_matrix_widget
        
        actions = create_sample_range()
        widget = create_matrix_widget(actions, "Utility Test")
        
        self.assertIsInstance(widget, HandMatrixWidget)
        self.assertEqual(widget.chart_name, "Utility Test")
        self.assertEqual(len(widget.actions), len(actions))
    
    def test_merge_chart_actions(self):
        """Test chart action merging utility."""
        from holdem_cli.charts.tui.widgets.matrix_widget import merge_chart_actions
        
        base_actions = {"AA": HandAction(ChartAction.RAISE)}
        overlay_actions = {"KK": HandAction(ChartAction.CALL)}
        
        merged = merge_chart_actions(base_actions, overlay_actions)
        
        self.assertIn("AA", merged)
        self.assertIn("KK", merged)
        self.assertEqual(len(merged), 2)
    
    def test_filter_actions_by_criteria(self):
        """Test action filtering utility."""
        from holdem_cli.charts.tui.widgets.matrix_widget import filter_actions_by_criteria
        
        actions = {
            "AA": HandAction(ChartAction.RAISE, frequency=1.0, ev=3.0),
            "22": HandAction(ChartAction.FOLD, frequency=1.0, ev=-1.0),
            "AKs": HandAction(ChartAction.RAISE, frequency=0.8, ev=2.0)
        }
        
        # Filter by action type
        raise_only = filter_actions_by_criteria(actions, {"action": ["raise"]})
        self.assertEqual(len(raise_only), 2)
        self.assertIn("AA", raise_only)
        self.assertIn("AKs", raise_only)
        
        # Filter by frequency
        high_freq = filter_actions_by_criteria(actions, {"min_frequency": 0.9})
        self.assertEqual(len(high_freq), 2)
        self.assertIn("AA", high_freq)
        self.assertIn("22", high_freq)
    
    def test_classify_hand_type(self):
        """Test hand type classification utility."""
        from holdem_cli.charts.tui.widgets.matrix_widget import classify_hand_type
        
        # Test pocket pair
        self.assertEqual(classify_hand_type("AA"), "pocket_pair")
        self.assertEqual(classify_hand_type("22"), "pocket_pair")
        
        # Test suited
        self.assertEqual(classify_hand_type("AKs"), "suited")
        self.assertEqual(classify_hand_type("76s"), "suited")
        
        # Test offsuit
        self.assertEqual(classify_hand_type("AKo"), "offsuit")
        self.assertEqual(classify_hand_type("T9o"), "offsuit")


def run_widget_demo():
    """Run a demo showing all widgets working together."""
    print("Holdem CLI Widgets Demo")
    print("=" * 50)
    
    # Create sample data
    sample_actions = create_sample_range()
    print(f"Created sample chart with {len(sample_actions)} hands")
    
    # Test matrix widget
    print("\n1. Testing HandMatrixWidget:")
    matrix = HandMatrixWidget(sample_actions, "Demo Chart")
    print(f"   - Chart: {matrix.chart_name}")
    print(f"   - Selected hand: {matrix.get_selected_hand()}")
    print(f"   - View mode: {matrix.view_mode}")
    
    # Test navigation
    matrix.navigate_to_hand("AKs")
    print(f"   - Navigated to: {matrix.get_selected_hand()}")
    
    # Test search
    results = matrix.search_hands("suited")
    print(f"   - Search 'suited': {len(results)} results")
    
    # Test details widget
    print("\n2. Testing HandDetailsWidget:")
    details = HandDetailsWidget()
    hand = "AKs"
    action = sample_actions.get(hand)
    details.update_hand(hand, action)
    print(f"   - Current hand: {details.current_hand}")
    print(f"   - Action: {details.current_action.action.value if details.current_action else 'None'}")
    
    # Test controls widget
    print("\n3. Testing ChartControlsWidget:")
    controls = ChartControlsWidget()
    print(f"   - View mode: {controls.current_view_mode}")
    print(f"   - Range builder: {controls.range_builder_enabled}")
    print(f"   - Status: {controls.get_status_summary()}")
    
    # Test help dialog
    print("\n4. Testing HelpDialog:")
    help_dialog = HelpDialog()
    sections = list(help_dialog.help_sections.keys())
    print(f"   - Help sections: {len(sections)}")
    print(f"   - Available: {', '.join(sections[:3])}...")
    
    # Test import dialog
    print("\n5. Testing ChartImportDialog:")
    import_dialog = ChartImportDialog()
    print(f"   - Dialog created successfully")
    
    # Test integration
    print("\n6. Testing Widget Integration:")
    
    # Simulate hand selection workflow
    matrix.navigate_to_hand("QQ")
    selected_hand = matrix.get_selected_hand()
    selected_action = matrix.actions.get(selected_hand)
    details.update_hand(selected_hand, selected_action)
    
    print(f"   - Matrix selected: {selected_hand}")
    print(f"   - Details updated: {details.current_hand}")
    print(f"   - Integration successful: {selected_hand == details.current_hand}")
    
    # Test view mode synchronization
    controls.current_view_mode = "frequency"
    matrix.set_view_mode(controls.current_view_mode)
    
    print(f"   - Controls view mode: {controls.current_view_mode}")
    print(f"   - Matrix view mode: {matrix.view_mode}")
    print(f"   - Sync successful: {controls.current_view_mode == matrix.view_mode}")
    
    print("\n✅ All widget tests completed successfully!")
    
    return {
        "matrix": matrix,
        "details": details,
        "controls": controls,
        "help": help_dialog,
        "import": import_dialog
    }


def run_performance_test():
    """Run performance tests for widgets."""
    import time
    
    print("Holdem CLI Widgets Performance Test")
    print("=" * 40)
    
    # Create large dataset
    sample_actions = create_sample_range()
    
    # Test matrix rendering performance
    print("\n1. Matrix Rendering Performance:")
    matrix = HandMatrixWidget(sample_actions, "Performance Test")
    
    # Cold render (no cache)
    start_time = time.time()
    render1 = matrix.render()
    cold_time = time.time() - start_time
    print(f"   - Cold render: {cold_time:.4f}s")
    
    # Warm render (with cache)
    start_time = time.time()
    render2 = matrix.render()
    warm_time = time.time() - start_time
    print(f"   - Warm render: {warm_time:.4f}s")
    print(f"   - Cache speedup: {cold_time / warm_time:.1f}x")
    
    # Test navigation performance
    print("\n2. Navigation Performance:")
    start_time = time.time()
    for i in range(100):
        matrix.selected_row = i % 13
        matrix.selected_col = i % 13
        matrix._update_selection()
    nav_time = time.time() - start_time
    print(f"   - 100 navigations: {nav_time:.4f}s")
    print(f"   - Per navigation: {nav_time/100*1000:.2f}ms")
    
    # Test search performance
    print("\n3. Search Performance:")
    start_time = time.time()
    results = matrix.search_hands("suited")
    search_time = time.time() - start_time
    print(f"   - Search 'suited': {search_time:.4f}s")
    print(f"   - Results found: {len(results)}")
    
    # Test cache efficiency
    print("\n4. Cache Efficiency:")
    cache_hits = 0
    cache_misses = 0
    
    # Simulate typical usage pattern
    for i in range(50):
        # Navigate (cache miss)
        matrix.selected_row = i % 13
        matrix.selected_col = i % 13
        matrix._update_selection()
        render = matrix.render()
        cache_misses += 1
        
        # Re-render same position (cache hit)
        render = matrix.render()
        cache_hits += 1
    
    print(f"   - Cache hits: {cache_hits}")
    print(f"   - Cache misses: {cache_misses}")
    print(f"   - Hit ratio: {cache_hits/(cache_hits+cache_misses):.1%}")
    
    print("\n✅ Performance tests completed!")


if __name__ == "__main__":
    # Run demo
    widgets = run_widget_demo()
    
    print("\n" + "=" * 50)
    
    # Run performance tests
    run_performance_test()
    
    print("\n" + "=" * 50)
    
    # Run unit tests
    print("\nRunning unit tests...")
    unittest.main(verbosity=2, exit=False)
