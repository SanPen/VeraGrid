cmake_minimum_required(VERSION 3.16)
project(VeraGridGeneratedFMU C)

if(NOT DEFINED VG_MODEL_IDENTIFIER)
  set(VG_MODEL_IDENTIFIER generated_model)
endif()

add_library(${VG_MODEL_IDENTIFIER} SHARED
  src/runtime_fmi2.c
  src/model_instance.c
  src/solver.c
  src/generated_model.c
  src/generated_procedural.c
)

target_include_directories(${VG_MODEL_IDENTIFIER}
  PRIVATE
    include
    src
)

if(MSVC)
  target_compile_definitions(${VG_MODEL_IDENTIFIER} PRIVATE _CRT_SECURE_NO_WARNINGS)
endif()

if(UNIX AND NOT APPLE)
  target_link_libraries(${VG_MODEL_IDENTIFIER} PRIVATE m)
endif()

set_target_properties(${VG_MODEL_IDENTIFIER} PROPERTIES
  PREFIX ""
  OUTPUT_NAME ${VG_MODEL_IDENTIFIER}
)
