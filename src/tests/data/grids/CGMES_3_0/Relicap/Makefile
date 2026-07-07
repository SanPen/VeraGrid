# List from https://github.com/entsoe/relicapgrid/issues/131
# We use ./referenceData/*/ttl/* because of https://github.com/entsoe/relicapgrid/issues/147

DIRS =                          \
  ./Belgovia/Grid               \
  ./Belgovia/NetworkCode        \
  ./Britheim/Grid               \
  ./DC-Espheim-Svedala/Grid     \
  ./DC-Nordheim-Galia/Grid      \
  ./Espheim/Grid                \
  ./Espheim/NetworkCode         \
  ./Galia/Grid                  \
  ./Galia/NetworkCode           \
  ./Jotunheim/Grid              \
  ./Nordheim/Grid               \
  ./Svedala/Grid                \
  ./Svedala/NetworkCode         \
  ./boundaryData/Grid           \
  ./commonData/Grid             \
  ./commonData/NetworkCode

DIRS_NEW = $(patsubst %, %/trig, $(DIRS))
CIMXML   = $(wildcard $(patsubst %,%/cimxml/*.xml,$(DIRS)))
TRIG     = $(subst cimxml,trig,$(subst .xml,.trig,$(CIMXML)))
TTL      = $(patsubst %,%/manifest.ttl,$(DIRS)) $(wildcard referenceData/*/ttl/*)

targets:
	echo targets: dirs, echo, trig, validate, zip

echo:
	@echo $(TRIG) $(TTL)

validate:
	riot --validate $(TRIG) $(TTL)

dirs:
	mkdir $(DIRS_NEW)

define CIMXML2TRIG
$(2): $(1)
	perl ../tools/fix-namespaces.pl $(1) | perl ../tools/cim-urn-uuid.pl > temp.xml
	perl ../tools/cim-trig.pl -r temp.xml > temp.trig
	update.bat --update=../tools/fix-datatypes-and-model.ru --data=temp.trig --dump > $(2)
	rm temp.xml temp.trig
endef

$(foreach x,$(CIMXML),$(eval $(call CIMXML2TRIG,$(x),$(subst cimxml,trig,$(subst .xml,.trig,$(x))))))

trig: $(TRIG)

zip: $(TRIG) $(TTL)
	zip -9 -u -o relicapgrid-CGM-trig.zip $^
