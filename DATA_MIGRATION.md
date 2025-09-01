# 🚀 EMS Inventory System - Data Migration Guide

## Overview
This guide will help you transfer your test data from the local development environment to your production Render deployment.

## 📋 **Migration Options**

### **Option 1: JSON Export/Import (Recommended)**
- ✅ **Pros:** Clean, safe, selective data transfer
- ✅ **Pros:** Easy to review and modify before import
- ✅ **Pros:** Handles data validation and conflicts
- ❌ **Cons:** Requires manual mapping for complex relationships

### **Option 2: Direct Database Copy**
- ✅ **Pros:** Complete data transfer, preserves all relationships
- ❌ **Cons:** Risk of overwriting production data
- ❌ **Cons:** Requires database access and technical expertise

### **Option 3: Manual Recreation**
- ✅ **Pros:** Clean slate, no data conflicts
- ❌ **Cons:** Time-consuming, potential for errors

---

## 🎯 **Recommended Approach: JSON Export/Import**

### **Step 1: Export Data from Local Environment**

1. **Run the export script:**
   ```bash
   source venv/bin/activate
   python export_data.py
   ```

2. **Verify export files:**
   ```bash
   ls -la data_export/
   # Should show:
   # - users.json
   # - locations.json
   # - items.json
   # - inventories.json
   # - inventory_items.json
   # - audit_logs.json
   # - export_summary.json
   ```

3. **Review the data:**
   ```bash
   cat data_export/export_summary.json
   ```

### **Step 2: Prepare Data for Production**

1. **Review and clean the data:**
   - Remove any test/sample data you don't want in production
   - Verify user accounts and permissions
   - Check item configurations

2. **Modify data if needed:**
   - Edit JSON files to remove sensitive information
   - Update email addresses for production
   - Adjust quantities or thresholds

### **Step 3: Import to Production**

#### **Method A: Render Shell (Recommended)**

1. **Go to your Render dashboard**
2. **Click on your service**
3. **Go to "Shell" tab**
4. **Upload your data_export folder** (drag and drop)
5. **Run the import script:**
   ```bash
   python import_data.py
   ```

#### **Method B: Git Repository**

1. **Add data_export folder to your repository:**
   ```bash
   git add data_export/
   git commit -m "Add data export for production import"
   git push origin master
   ```

2. **Render will auto-deploy** with the data files
3. **Run import script** via Render shell

---

## 🔧 **Data Import Details**

### **What Gets Imported:**
- ✅ **Users** - All user accounts (with default password 'changeme123')
- ✅ **Locations** - All location definitions
- ✅ **Items** - All item definitions and configurations
- ⚠️ **Inventories** - Skipped (requires complex location mapping)
- ⚠️ **Inventory Items** - Skipped (requires complex ID mapping)
- ❌ **Audit Logs** - Skipped (not needed in production)

### **Import Process:**
1. **Checks for existing data** to avoid duplicates
2. **Validates data integrity** before import
3. **Handles errors gracefully** with rollback
4. **Provides detailed logging** of the import process

---

## 🚨 **Important Security Notes**

### **After Import:**
1. **Change all user passwords** from default 'changeme123'
2. **Verify user permissions** are correct
3. **Review admin access** and remove any test accounts
4. **Check email addresses** are production-ready

### **Data Validation:**
1. **Verify all locations** imported correctly
2. **Check item configurations** match expectations
3. **Test user login** with new passwords
4. **Verify admin functionality** works as expected

---

## 🛠️ **Troubleshooting**

### **Common Issues:**

#### **Import Fails with Database Error:**
```bash
# Check database connection
python -c "from app import create_app; app = create_app(); print('DB OK')"
```

#### **Data Not Importing:**
```bash
# Check file permissions
ls -la data_export/
# Verify JSON files are valid
python -m json.tool data_export/users.json
```

#### **Duplicate Data:**
- The import script automatically skips existing records
- Check the import logs for skipped items
- Manually remove duplicates if needed

---

## 📊 **Post-Import Verification**

### **Check These Items:**
1. **User Accounts:**
   - [ ] All users can log in
   - [ ] Admin permissions work correctly
   - [ ] Passwords changed from default

2. **Locations:**
   - [ ] All locations appear in the system
   - [ ] Location types are correct
   - [ ] Descriptions are complete

3. **Items:**
   - [ ] All items are visible
   - [ ] Required quantities are set
   - [ ] Thresholds are appropriate

4. **System Functionality:**
   - [ ] Can create new inventories
   - [ ] Search and filter work
   - [ ] Reports generate correctly

---

## 🔄 **Advanced: Full Data Migration**

If you need to migrate **everything** including inventories and inventory items:

### **Step 1: Enhanced Export Script**
Modify `export_data.py` to include location name mapping:
```python
# Add location name to export
location_data = {
    'id': location.id,  # Include original ID
    'name': location.name,
    # ... other fields
}
```

### **Step 2: Enhanced Import Script**
Modify `import_data.py` to handle ID mappings:
```python
# Create ID mapping tables
old_to_new_ids = {}
for old_location in old_locations:
    new_location = Location.query.filter_by(name=old_location['name']).first()
    old_to_new_ids[old_location['id']] = new_location.id
```

### **Step 3: Import with Relationships**
Use the mapping to recreate inventories and inventory items with correct relationships.

---

## 📝 **Migration Checklist**

- [ ] **Export local data** using `export_data.py`
- [ ] **Review exported data** for accuracy
- [ ] **Upload data files** to Render
- [ ] **Run import script** in Render shell
- [ ] **Verify all data** imported correctly
- [ ] **Change user passwords** from default
- [ ] **Test system functionality** thoroughly
- [ ] **Remove test data** from local environment
- [ ] **Update documentation** with production details

---

## 🎉 **Success!**

After completing the migration:
- Your production system will have all your test data
- Users can log in with new passwords
- All locations and items are configured
- You can start using the system immediately

**Remember:** Always test thoroughly in production before going live with real users!
