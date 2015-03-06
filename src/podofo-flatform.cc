/* Copyright (c) 2015, Djaodjin Inc.
   All rights reserved.

  Redistribution and use in source and binary forms, with or without
  modification, are permitted provided that the following conditions are met:

  1. Redistributions of source code must retain the above copyright notice,
     this list of conditions and the following disclaimer.
  2. Redistributions in binary form must reproduce the above copyright notice,
     this list of conditions and the following disclaimer in the documentation
     and/or other materials provided with the distribution.

  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
  AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
  WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
  OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
  ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
*/

#include <stdlib.h>
#include <iostream>
#include <cstdio>
#include <podofo/podofo.h>

#ifndef PRINT_DEBUG_MSG
#define PRINT_DEBUG_MSG           0
#endif


using namespace PoDoFo;

/** For debugging, print (key, data_type) on stderr.
 */
void show_dict( const PdfDictionary& dict, const char *indent = "" )
{
    TKeyMap keys = dict.GetKeys();
    for( TCIKeyMap iter = keys.begin(); iter != keys.end(); ++iter ) {
        const char *str = iter->second->GetDataTypeString();
        std::cerr << indent << iter->first.GetName()
                  << ":" << str
                  << std::endl;
    }
}

/** Set the value in an input text *field*. The value is taken from *fills*,
    a map indexed by field names.

    In some PDF files the field_name is not directly associated to the input
    object ("T") but to its "Parent".

    Chrome does not respect the read-only flag (Preview.app does),
    so we typically don't use this function in production. We prefer
    ``flat_text_field`` instead.
 */
void
fill_text_field( PdfTextField& field,
    const std::map<std::string, std::string>& fills )
{
#if PRINT_DEBUG_MSG
    std::cerr << "field:\n";
    TKeyMap keys = field.GetFieldObject()->GetDictionary().GetKeys();
    for( TCIKeyMap iter = keys.begin(); iter != keys.end(); ++iter ) {
        std::cerr << iter->first.GetName();
        try {
            if( iter->second->IsDictionary() ) {
                const PdfDictionary& dict = iter->second->GetDictionary();
                show_dict(dict, "\t\t");

            } else if( iter->second->IsReference() ) {
                const PdfReference& ref = iter->second->GetReference();
                PdfObject *obj = field.GetFieldObject()->GetOwner()->GetObject(ref);
                if( obj->IsDictionary() ) {
                    TKeyMap parent_keys = obj->GetDictionary().GetKeys();
                    for( TCIKeyMap parent_iter = parent_keys.begin();
                         parent_iter != parent_keys.end(); ++parent_iter ) {
                        std::cerr << "\t" << parent_iter->first.GetName();
                        const char *str = parent_iter->second->GetDataTypeString();
                        std::cerr << ":" << str;
                        if( parent_iter->first.GetName() == "T" ) {
                            std::cerr << ":"
                                << parent_iter->second->GetString().GetString();
                        }
                        std::cerr << std::endl;
                    }
                } else {
                    std::cerr << ":" << obj->GetDataTypeString();
                    std::cerr << " :" << ref.ToString() << std::endl;
                }
            } else {
                const char *str = iter->second->GetDataTypeString();
                std::cerr << ":" << str << std::endl;
            }
        } catch( PdfError& err ) {
            std::cerr << ":" << "<error>" << std::endl;
        }
    }
#endif

    // PdfTextField::GetFieldName()
    const char* field_name = "";
    if( field.GetFieldName().IsValid() ) {
        field_name = field.GetFieldName().GetString();
    } else {
        PdfObject *obj = field.GetFieldObject();
        if( obj->GetDictionary().HasKey(PdfName("Parent")) ) {
            const PdfReference& ref = obj->GetDictionary().GetKey(
                PdfName("Parent"))->GetReference();
            obj = obj->GetOwner()->GetObject(ref);
            field_name = obj->GetDictionary().GetKey(
                PdfName("T"))->GetString().GetString();
        }
    }

    std::map<std::string, std::string>::const_iterator found
        = fills.find(std::string(field_name));
    if( found != fills.end() ) {
#if PRINT_DEBUG_MSG
        std::cerr << "Set '"<< field_name << "' to '" << found->second << "'\n";
#endif
        // PdfTextField::SetText()
        PdfName key = field.IsRichText() ? PdfName("RV") : PdfName("V");
        PdfObject *obj = field.GetFieldObject();
        if( !obj->GetDictionary().HasKey(PdfName("T")) ) {
            const PdfReference& ref = obj->GetDictionary().GetKey(
                PdfName("Parent"))->GetReference();
            obj = obj->GetOwner()->GetObject(ref);
        }
        // if field value is longer than maxlen, truncate it
        pdf_long nMax = field.GetMaxLen();
        if( (nMax != -1) && (found->second.size() > nMax) )
            obj->GetDictionary().AddKey(
                key, PdfString(found->second.c_str(), nMax));
        else
            obj->GetDictionary().AddKey(key, PdfString(found->second.c_str()));
#if PRINT_DEBUG_MSG
    } else {
        std::cerr << "warning: no value for field '"<< field_name << "'\n";
#endif
    }
    field.SetReadOnly(true);
}

/** Draw an input field (*annot*) value taken from *fills*, a map indexed by
    field names, at the position the input field appears in the document.

    In some PDF files the field_name is not directly associated to the input
    object ("T") but to its "Parent".
*/
void flat_text_field( PdfAnnotation* annot,
    const std::map<std::string, std::string>& fills,
    PdfPainter& painter,
    PdfDocument& doc ) {
    std::string font_family("Helvetica");
    int font_size = 12;

    if( annot->GetObject()->GetDictionary().HasKey(PdfName("DA")) ) {
        PdfObject *da_obj
            = annot->GetObject()->GetDictionary().GetKey(PdfName("DA"));
        std::string da_value(da_obj->GetString().GetString());
        size_t start = da_value.find('/');
        size_t end = da_value.find("Tf");
        for( --end; end > 0 && (
                da_value[end] == ' ' || isdigit(da_value[end])); --end ) {}
        std::string font_family = da_value.substr(start + 1, end - start);
        font_size = atoi(da_value.substr(end + 1).c_str());
#if PRINT_DEBUG_MSG
        std::cerr << "field DA: " << da_obj->GetString().GetString()
                  << std::endl;
        std::cerr << "\tfont-family: " << font_family
                  << ", font-size: " << font_size
                  << std::endl;
#endif
    }

    painter.SetFont(doc.CreateFont(font_family.c_str()));
    painter.GetFont()->SetFontSize(font_size);
    const PdfRect& rect = annot->GetRect();

    // PdfTextField::GetFieldName() for Annotation
    const char* field_name = "";
    PdfString pdf_field_name;
    PdfObject *obj = annot->GetObject();
    if( obj->GetDictionary().HasKey(PdfName("T")) ) {
        pdf_field_name = obj->GetDictionary().GetKey(PdfName("T"))->GetString();
    }
    if( pdf_field_name.IsValid() ) {
        field_name = pdf_field_name.GetString();
    } else {
        if( obj->GetDictionary().HasKey(PdfName("Parent")) ) {
            const PdfReference& ref = obj->GetDictionary().GetKey(
                PdfName("Parent"))->GetReference();
            obj = obj->GetOwner()->GetObject(ref);
            field_name = obj->GetDictionary().GetKey(
                PdfName("T"))->GetString().GetString();
        }
    }

    std::map<std::string, std::string>::const_iterator found
        = fills.find(std::string(field_name));
    if( found != fills.end() ) {
#if PRINT_DEBUG_MSG
        std::cerr << "Set '"<< field_name << "' to '" << found->second << "'\n";
#endif
        painter.DrawText(
            rect.GetLeft(), rect.GetBottom() + 1, found->second.c_str());
#if PRINT_DEBUG_MSG
    } else {
        std::cerr << "warning: no value for field '"<< field_name << "'\n";
#endif
    }
}


void
flat_form( const std::string& output_path, const std::string& input_path,
    const std::map<std::string, std::string>& fills )
{
    PdfMemDocument doc(input_path.c_str());
    PdfPainter painter;

    int nb_pages = doc.GetPageCount();
    for( int i = 0; i < nb_pages; ++i ) {
        PdfPage *page = doc.GetPage(i);
        painter.SetPage(page);

        int nb_fields = page->GetNumFields();
        for( int n = 0; n < nb_fields; ++n ) {
            PdfField field = page->GetField(n);
            EPdfField eType = field.GetType();

            switch( eType ) {
               case ePdfField_TextField:
                {
                    PdfTextField text(field);
                    flat_text_field(
                        page->GetAnnotation(n), fills, painter, doc);
                    break;
                }
                default:
                    break;
            }
        }
        painter.FinishPage();

        /* Delete annotations to make sure fields cannot be written over. */
        for( int n = 0; n < nb_fields; ++n ) {
            page->DeleteAnnotation(0);
        }
    }

    if( output_path != "-" ) {
        doc.Write(output_path.c_str());
    } else {
        PdfOutputDevice out(&std::cout);
        doc.Write(&out);
    }
}


int main( int argc, char* argv[] )
{
    int idx = 1;
    std::string input_path, output_path;
    std::map<std::string, std::string> fills;

    while( idx < argc ) {
        if( strncmp(argv[idx], "--fill", 6) == 0 ) {
            ++idx;
            if( idx >= argc ) {
                std::cerr << "missing field_name=field_value after --fill\n";
                return 1;
            }
            const char *sep = strchr(argv[idx], '=');
            if( !sep ) {
                std::cerr
                    << "no separator field_name=field_value after --fill\n";
                return 1;
            }
            fills[std::string(argv[idx], sep - argv[idx])]
                = std::string(sep + 1);
        } else if( input_path.empty() ) {
            input_path = std::string(argv[idx]);
        } else {
            output_path = std::string(argv[idx]);
        }
        ++idx;
    }

    if( input_path.empty() || output_path.empty() ) {
        std::cout << "Usage: " << argv[0]
            << " [--fill field_name=field_value] input_file output_file\n";
        std::cout << "Fill out an existing form and save it to a PDF file\n";
        return 1;
    }

    flat_form(output_path, input_path, fills);
    return 0;
}
