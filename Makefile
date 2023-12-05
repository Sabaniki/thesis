BUILD_DIR = ./build
SRC_DIR = ./src
# SRC_DIR = ./
SRCS = $(shell ls $(SRC_DIR)/*.tex)

BASE = thesis
MAIN_TEX = ./$(BASE).tex
DATE = `date "+%Y%m%d%H"`
MAIN_PDF = $(MAIN_TEX:$(SRC_DIR)/%.tex=$(BUILD_DIR)/%.pdf)

REDPEN := $(if $(REDPEN),$(REDPEN),redpen --conf redpen-conf.xml --result-format xml)
all: build

.PHONY: build
build: $(MAIN_PDF)

.PHONY: $(MAIN_PDF)
$(MAIN_PDF): $(BUILD_DIR)/$(SRC_DIR)
	latexmk -pdfdvi $(PREVIEW_CONTINUOUSLY) -use-make $(MAIN_TEX)

$(BUILD_DIR)/$(SRC_DIR):
	mkdir -p $@

snapshot: build
	mkdir -p output/snapshot
	cp $(MAIN_PDF) output/snapshot/$(BASE)_$(DATE).pdf

.PHONY: watch
watch: PREVIEW_CONTINUOUSLY=-pvc
watch: build

.PHONY: redpen
redpen: redpen.ja #redpen.en

redpen.%: $(shell echo $(SRC_DIR)/*.%.tex)
	$(REDPEN) \
	--result-format xml \
	--lang ja \
	--conf redpen/redpen.$(subst redpen.,,$@).xml \
	$^ > build/$@.xml
	@echo "<!-- generated by 'make $@' -->" >> build/$@.xml

.PHONY: clean
clean:
	@$(RM) -rf $(BUILD_DIR)/*
