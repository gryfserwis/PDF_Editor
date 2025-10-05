#!/usr/bin/env python3
"""
Final comprehensive test to validate all changes
"""

import sys
import os
import json

def test_all_changes():
    """Run all validation tests"""
    
    print("="*80)
    print("FINAL COMPREHENSIVE TEST FOR MACRO SYSTEM IMPROVEMENTS")
    print("="*80)
    print()
    
    # Read the PDFEditor.py file
    with open('/home/runner/work/PDF_Editor/PDF_Editor/PDFEditor.py', 'r') as f:
        content = f.read()
    
    all_tests_passed = True
    
    # Test 1: Menu structure
    print("TEST 1: Menu Structure Changes")
    print("-" * 40)
    menu_section = content[content.find('# === MENU MAKRA ==='):content.find('# === MENU MAKRA ===') + 500]
    
    if 'label="Nagraj makro..."' not in menu_section:
        print("✓ 'Nagraj makro...' removed from Makra menu")
    else:
        print("✗ FAIL: 'Nagraj makro...' still in menu")
        all_tests_passed = False
    
    if 'label="Lista makr użytkownika..."' in menu_section:
        print("✓ 'Lista makr użytkownika...' remains in menu")
    else:
        print("✗ FAIL: Menu item missing")
        all_tests_passed = False
    print()
    
    # Test 2: MacrosListDialog changes
    print("TEST 2: MacrosListDialog UI Changes")
    print("-" * 40)
    macros_list_section = content[content.find('class MacrosListDialog'):content.find('class MacrosListDialog') + 10000]
    
    if 'buttons_frame.pack(side="right"' in macros_list_section:
        print("✓ Buttons repositioned to right side")
    else:
        print("✗ FAIL: Buttons not on right side")
        all_tests_passed = False
    
    if 'text="Nagraj makro..."' in macros_list_section and 'command=self.record_macro' in macros_list_section:
        print("✓ 'Nagraj makro...' button added to dialog")
    else:
        print("✗ FAIL: 'Nagraj makro...' button missing")
        all_tests_passed = False
    
    if 'def record_macro(self):' in macros_list_section:
        print("✓ record_macro() method added")
    else:
        print("✗ FAIL: record_macro() method missing")
        all_tests_passed = False
    print()
    
    # Test 3: MacroRecordingDialog changes
    print("TEST 3: MacroRecordingDialog Changes")
    print("-" * 40)
    recording_section = content[content.find('class MacroRecordingDialog'):content.find('class MacroRecordingDialog') + 10000]
    
    if 'Funkcje które mogą zostać nagrane' in recording_section:
        print("✓ Function list label added")
    else:
        print("✗ FAIL: Function list label missing")
        all_tests_passed = False
    
    required_functions = [
        'Obróć w lewo / w prawo',
        'Zaznacz wszystkie',
        'Przesuń zawartość strony',
        'Dodaj numerację stron',
        'Usuń numerację stron',
        'Kadruj / Zmień rozmiar'
    ]
    
    missing_functions = []
    for func in required_functions:
        if func not in recording_section:
            missing_functions.append(func)
    
    if not missing_functions:
        print("✓ All recordable functions listed")
    else:
        print(f"✗ FAIL: Missing functions: {missing_functions}")
        all_tests_passed = False
    print()
    
    # Test 4: MacroEditDialog changes
    print("TEST 4: MacroEditDialog Changes")
    print("-" * 40)
    edit_section = content[content.find('class MacroEditDialog'):content.find('class MacroEditDialog') + 10000]
    
    if 'self.actions_text = tk.Text' in edit_section:
        print("✓ Changed to Text widget")
    else:
        print("✗ FAIL: Not using Text widget")
        all_tests_passed = False
    
    if 'self.actions_listbox' in edit_section:
        print("✗ FAIL: Listbox still present")
        all_tests_passed = False
    else:
        print("✓ Listbox removed")
    
    if 'json.dumps(self.actions' in edit_section:
        print("✓ JSON serialization used")
    else:
        print("✗ FAIL: JSON serialization not used")
        all_tests_passed = False
    
    if 'json.loads(' in edit_section:
        print("✓ JSON parsing used")
    else:
        print("✗ FAIL: JSON parsing not used")
        all_tests_passed = False
    
    if 'def move_up' in edit_section or 'def move_down' in edit_section:
        print("✗ FAIL: Old move buttons still present")
        all_tests_passed = False
    else:
        print("✓ Move up/down methods removed")
    print()
    
    # Test 5: Removed _record_action calls
    print("TEST 5: Unsupported Actions Removed")
    print("-" * 40)
    
    unsupported_actions = [
        ('copy', "copy_selected_pages"),
        ('cut', "cut_selected_pages"),
        ('paste_before', "_handle_paste_operation"),
        ('delete', "delete_selected_pages"),
        ('duplicate', "duplicate_selected_page"),
        ('swap', "swap_pages"),
        ('insert_blank', "_insert_blank_page")
    ]
    
    removed_count = 0
    for action, method in unsupported_actions:
        search_pattern = f"_record_action('{action}"
        if search_pattern not in content:
            removed_count += 1
        else:
            print(f"✗ FAIL: _record_action('{action}') still present")
            all_tests_passed = False
    
    if removed_count == len(unsupported_actions):
        print(f"✓ All {len(unsupported_actions)} unsupported _record_action calls removed")
    print()
    
    # Test 6: run_macro() changes
    print("TEST 6: run_macro() Method Changes")
    print("-" * 40)
    run_macro_section = content[content.find('def run_macro(self, macro_name):'):content.find('def run_macro(self, macro_name):') + 5000]
    
    unsupported_methods = [
        'delete_selected_pages',
        'duplicate_selected_page',
        'copy_selected_pages',
        'cut_selected_pages',
        'paste_pages_before',
        'paste_pages_after',
        'swap_pages',
        'insert_blank_page_before',
        'insert_blank_page_after'
    ]
    
    found_unsupported = []
    for method in unsupported_methods:
        if method in run_macro_section:
            found_unsupported.append(method)
    
    if not found_unsupported:
        print("✓ All unsupported methods removed from run_macro()")
    else:
        print(f"✗ FAIL: Found unsupported methods: {found_unsupported}")
        all_tests_passed = False
    
    # Check that supported methods are still there
    supported_methods = [
        'rotate_selected_page',
        '_select_all',
        '_select_odd_pages',
        '_select_even_pages',
        '_select_portrait_pages',
        '_select_landscape_pages'
    ]
    
    missing_supported = []
    for method in supported_methods:
        if method not in run_macro_section:
            missing_supported.append(method)
    
    if not missing_supported:
        print("✓ All supported methods still in run_macro()")
    else:
        print(f"✗ FAIL: Missing supported methods: {missing_supported}")
        all_tests_passed = False
    print()
    
    # Test 7: Replay functions implemented
    print("TEST 7: Replay Functions Implementation")
    print("-" * 40)
    
    replay_functions = [
        ('_replay_insert_page_numbers', 'insert_text'),
        ('_replay_remove_page_numbers', 'add_redact_annot'),
        ('_replay_apply_page_crop_resize', '_mask_crop_pages')
    ]
    
    for func_name, key_operation in replay_functions:
        func_start = content.find(f'def {func_name}(self, params):')
        if func_start == -1:
            print(f"✗ FAIL: {func_name} not found")
            all_tests_passed = False
            continue
        
        func_section = content[func_start:func_start + 10000]
        
        # Check it's not just a stub
        if 'pominięto' in func_section or 'parametryzacji' in func_section:
            print(f"✗ FAIL: {func_name} is still a stub")
            all_tests_passed = False
        elif key_operation in func_section:
            print(f"✓ {func_name} fully implemented")
        else:
            print(f"✗ FAIL: {func_name} implementation incomplete")
            all_tests_passed = False
    print()
    
    # Test 8: Parameter recording completeness
    print("TEST 8: Parameter Recording Completeness")
    print("-" * 40)
    
    insert_numbers_record = content[content.find("_record_action('insert_page_numbers'"):content.find("_record_action('insert_page_numbers'") + 500]
    
    required_params = [
        'start_num',
        'mode',
        'alignment',
        'vertical_pos',
        'mirror_margins',
        'format_type',
        'margin_left_mm',
        'margin_right_mm',
        'margin_vertical_mm',
        'font_size',
        'font_name'
    ]
    
    missing_params = []
    for param in required_params:
        if param not in insert_numbers_record:
            missing_params.append(param)
    
    if not missing_params:
        print("✓ All parameters recorded for insert_page_numbers")
    else:
        print(f"✗ FAIL: Missing parameters: {missing_params}")
        all_tests_passed = False
    print()
    
    # Test 9: JSON validation logic
    print("TEST 9: JSON Validation Logic")
    print("-" * 40)
    
    save_method = content[content.find('class MacroEditDialog'):].find('def save(self):')
    if save_method != -1:
        save_section = content[content.find('class MacroEditDialog') + save_method:content.find('class MacroEditDialog') + save_method + 3000]
        
        validations = [
            ('json.loads(', 'JSON parsing'),
            ('isinstance(actions, list)', 'list validation'),
            ('not actions', 'empty check'),
            ("'action' not in action", 'action field check')
        ]
        
        all_validations_present = True
        for check, desc in validations:
            if check in save_section:
                print(f"✓ {desc} present")
            else:
                print(f"✗ FAIL: {desc} missing")
                all_validations_present = False
                all_tests_passed = False
        
        if all_validations_present:
            print("✓ All validation checks present")
    else:
        print("✗ FAIL: save() method not found")
        all_tests_passed = False
    print()
    
    # Test 10: Syntax check
    print("TEST 10: Python Syntax Validation")
    print("-" * 40)
    
    try:
        compile(content, 'PDFEditor.py', 'exec')
        print("✓ Python syntax is valid")
    except SyntaxError as e:
        print(f"✗ FAIL: Syntax error: {e}")
        all_tests_passed = False
    print()
    
    # Final summary
    print("="*80)
    if all_tests_passed:
        print("✓✓✓ ALL TESTS PASSED ✓✓✓")
        print("All 6 requirements have been successfully implemented and validated!")
    else:
        print("✗✗✗ SOME TESTS FAILED ✗✗✗")
        print("Please review the failures above")
    print("="*80)
    
    return all_tests_passed

if __name__ == "__main__":
    success = test_all_changes()
    sys.exit(0 if success else 1)
