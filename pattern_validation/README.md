# Pattern Validation & Testing

This folder contains all pattern validation scripts, test files, and documentation to keep the main repository clean and organized.

## 📁 Folder Structure

### **Active Validation Scripts:**
- `catapult_pattern_validator.py` - Comprehensive validation for catapult patterns
- `quick_catapult_test.py` - Quick functionality test for catapult patterns
- `CATAPULT_PATTERNS_IMPLEMENTATION_COMPLETE.md` - Complete documentation

### **Legacy Tests:**
- `legacy_tests/` - All previous test files moved from main repo for organization
  - Contains historical test scripts for various patterns and features
  - Includes debug scripts and development test files
  - Preserved for reference and future development

## 🚀 Usage

### **Running Catapult Pattern Validation:**
```bash
# Comprehensive validation
python pattern_validation/catapult_pattern_validator.py

# Quick test
python pattern_validation/quick_catapult_test.py
```

### **Creating New Pattern Validations:**
1. Create new validation script in this folder
2. Follow the naming convention: `{pattern_name}_validator.py`
3. Include comprehensive tests for pattern detection accuracy
4. Document results and implementation details

## 📊 Pattern Validation Guidelines

### **Validation Requirements:**
- ✅ Pattern detection accuracy
- ✅ Alert trigger verification
- ✅ One-time alert mechanism
- ✅ EMA validation (where applicable)
- ✅ Latest column focus for live trading
- ✅ Integration with existing alert system

### **Test Data Requirements:**
- Use realistic price movements
- Include proper P&F structure formation
- Test edge cases and false positives
- Validate against user-provided pattern images

## 🎯 Benefits of This Organization

1. **Clean Main Repository** - Core application code is uncluttered
2. **Organized Testing** - All validation scripts in one place
3. **Easy Reference** - Legacy tests preserved for future development
4. **Professional Structure** - Clear separation of concerns
5. **Scalable** - Easy to add new pattern validations

## 📝 Notes

- All validation scripts should be self-contained
- Include proper error handling and logging
- Document expected results and validation criteria
- Follow existing code style and conventions
