set(targetName Clib)
aux_source_directory(. src_list)
include_directories(../include)
add_library(${targetName} ${src_list})
