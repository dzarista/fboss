# FBOSS Heatmap Tool - Development Makefile

.PHONY: help test deploy

# Default target
help:
	@echo "FBOSS Heatmap Tool - Available Commands:"
	@echo "========================================"
	@echo "  make test          - Run all tests and validation"
	@echo "  make deploy        - Deploy to web server"

# Run comprehensive test suite with validation
test:
	@echo "🧪 Running FBOSS Heatmap Test Suite..."
	@echo ""
	@echo "🔧 Validating configuration files..."
	@node -e "try { JSON.parse(require('fs').readFileSync('./data_extraction_config.json', 'utf8')); console.log('✅ data_extraction_config.json is valid'); } catch(e) { console.error('❌ data_extraction_config.json is invalid:', e.message); process.exit(1); }"
	@node -e "try { JSON.parse(require('fs').readFileSync('./regex_patterns.json', 'utf8')); console.log('✅ regex_patterns.json is valid'); } catch(e) { console.error('❌ regex_patterns.json is invalid:', e.message); process.exit(1); }"
	@echo ""
	@echo "🔍 Running regex pattern validation..."
	@node test_regex_patterns.js
	@echo ""
	@echo "🧪 Running extraction tests..."
	@node test_suite.js
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
	@echo "🎉 All tests completed successfully!"

# Deploy to web server
deploy:
	@echo "🚀 Deploying to web server..."
	@rm -rf ~/public_html/llm/fboss_heatmap
	@cp -r . ~/public_html/llm/fboss_heatmap
	@echo "✅ Deployed to ~/public_html/llm/fboss_heatmap"
