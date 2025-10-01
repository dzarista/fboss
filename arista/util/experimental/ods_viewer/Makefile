# ODS Viewer Tool - Development Makefile

.PHONY: help test deploy clean

# Default target
help:
	@echo "ODS Viewer Tool - Available Commands:"
	@echo "===================================="
	@echo "  make test          - Run all tests and validation"
	@echo "  make deploy        - Deploy to web server"
	@echo "  make clean         - Clean up temporary files"

# Run comprehensive test suite with validation
test:
	@echo "🧪 Running ODS Viewer Test Suite..."
	@echo ""
	@echo "🔍 Running basic code checks..."
	@if find . -name "*.html" -o -name "*.js" -o -name "*.json" -o -name "*.csv" -o -name "*.md" | xargs grep -l '[[:space:]]$$' 2>/dev/null; then \
		echo "⚠️  Found files with trailing whitespace"; \
		find . -name "*.html" -o -name "*.js" -o -name "*.json" -o -name "*.csv" -o -name "*.md" | xargs sed -i 's/[[:space:]]*$$//'; \
		echo "✅ Trailing whitespace cleaned"; \
	else \
		echo "✅ No trailing whitespace found"; \
	fi
	@if grep -n "console\.log.*🔍\|console\.log.*DEBUG\|console\.log.*Test" index.html 2>/dev/null; then \
		echo "⚠️  Found debug console.log statements that should be removed for production"; \
	else \
		echo "✅ No problematic debug console.log statements found"; \
	fi
	@echo ""
	@echo "🧪 Running ODS data processing tests..."
	@node test_ods_processing.js
	@echo ""
	@echo "🔍 Validating HTML structure..."
	@if grep -q "Multi-File ODS Data Viewer" index.html; then \
		echo "✅ HTML title found"; \
	else \
		echo "❌ HTML title missing"; \
		exit 1; \
	fi
	@if grep -q "plotly-latest.min.js" index.html; then \
		echo "✅ Plotly.js dependency found"; \
	else \
		echo "❌ Plotly.js dependency missing"; \
		exit 1; \
	fi
	@if grep -q "papaparse.min.js" index.html; then \
		echo "✅ PapaParse dependency found"; \
	else \
		echo "❌ PapaParse dependency missing"; \
		exit 1; \
	fi
	@echo ""
	@echo "📊 Validating test data files..."
	@if [ -f "test_data/sample_time_series.csv" ]; then \
		echo "✅ Sample time series data found"; \
	else \
		echo "❌ Sample time series data missing"; \
		exit 1; \
	fi
	@if [ -f "test_data/large_ods_log_wlr_br.csv" ] || [ -f "test_data/large_ods_log_wlr_br.csv.gz" ]; then \
		echo "✅ Large ODS log data found"; \
	else \
		echo "⚠️  Large ODS log data not found (optional)"; \
	fi
	@echo ""
	@echo "🎉 All tests completed successfully!"

# Deploy to web server
deploy:
	@echo "🚀 Deploying ODS Viewer to web server..."
	@rm -rf ~/public_html/llm/ods_viewer
	@cp -r . ~/public_html/llm/ods_viewer
	@echo "✅ Deployed to ~/public_html/llm/ods_viewer"
	@echo ""
	@echo "🌐 Access at: https://usercontent.infra.corp.arista.io/~deank/llm/ods_viewer/"

# Clean up temporary files
clean:
	@echo "🧹 Cleaning up temporary files..."
	@find . -name "*.tmp" -delete 2>/dev/null || true
	@find . -name ".DS_Store" -delete 2>/dev/null || true
	@echo "✅ Cleanup completed"
