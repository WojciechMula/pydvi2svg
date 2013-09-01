/*
 * Font2Meta
 *
 * This simple utility use FreeType2 library to produce
 * on standard output some informations about glyphs:
 * - family name
 * - information about all glyphs:
 *    - name of glyph
 *    - value of X advance
 *    - set of commands need to draw outline
 *
 * Wojciech Mu³a
 * wojciech_mula@poczta.onet.pl
 *
 * compilation:
 *    gcc -I/usr/include/freetype2 -lfreetype fnt2meta -o your_favorite_name
 *
 * usage:
 *    your_favorite_name path_to_font_file
 *
 * pulic domain
 * last update: 2013-01-01
 */

#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>

#include <ft2build.h>
#include FT_FREETYPE_H

int move_to(const FT_Vector*, void*);
int line_to(const FT_Vector*, void*);
int conic_to(const FT_Vector*, const FT_Vector*, void*);
int cubic_to(const FT_Vector*, const FT_Vector*, const FT_Vector*, void*);

void print_error(char* msg, ...);
void print_warn(char* msg, ...);
int process_face(FT_Library library, char* name);

#define MAX_GLYPH_NAME 256

int main(int argc, char** argv) {
	FT_Library	library;
	FT_Error	error;

	if (argc < 2) {
		print_error("Not enought arguments");
		return EXIT_FAILURE;
	}

	error = FT_Init_FreeType(&library);
	if (error) {
		print_error("Can't initialize FreeType library");
		return EXIT_FAILURE;
	}


	int ret = process_face(library, argv[1]) ? EXIT_SUCCESS : EXIT_FAILURE;
	FT_Done_FreeType(library);

	return ret;
}

int process_face(FT_Library library, char* path) {
	FT_Error error;
	FT_Face  face;
	FT_Outline_Funcs funcs;
	char glyphname[MAX_GLYPH_NAME];
	int  i;

	error = FT_New_Face(library, path, 0, &face);
	if (error) {
		print_error("Can't read font '%s'", path);
		return 0;
	}

	/* process only fonts that defines glyph names */
	if (!FT_HAS_GLYPH_NAMES(face)) {
		FT_Done_Face(face);
		print_error("Font doesn't define glyph names");
		return 0;
	}

	funcs.move_to	= move_to;
	funcs.line_to	= line_to;
	funcs.conic_to	= conic_to;
	funcs.cubic_to	= cubic_to;
	funcs.shift	 	= 0;
	funcs.delta		= 0;

	/* display family name */
	printf("family %s\n", face->family_name);

	for (i=0; i < face->num_glyphs; i++) {
		error = FT_Load_Glyph(face, i, FT_LOAD_NO_SCALE);
		if (error) {
			/* just skip glyph if error */
			print_warn("Can't read glyph #%d, skipped", i+1);
			continue;
		}

		error = FT_Get_Glyph_Name(face, i, (FT_Pointer)glyphname, MAX_GLYPH_NAME);
		if (error) {
			print_warn("Can't read glyph name #%d, skipped", i+1);
			continue;
		}

		/* display font name */
		printf("char %s\n", glyphname);

		/* display horiz andvance x */
		printf("\tadv %ld\n", face->glyph->metrics.horiAdvance);

		error = FT_Outline_Decompose(&(face->glyph->outline), &funcs, NULL);
		printf("end\n");
	}

	FT_Done_Face(face);
	return 1;
}

void print_error(char* msg, ...) {
	va_list ap;

	fputs("ERROR: ", stderr);

	va_start(ap, msg);
	vfprintf(stderr, msg, ap);
	va_end(ap);

	fputc('\n', stderr);
}

void print_warn(char* msg, ...) {
	va_list ap;

	fputs("WARNING: ", stderr);

	va_start(ap, msg);
	vfprintf(stderr, msg, ap);
	va_end(ap);

	fputc('\n', stderr);
}

/* outline callbacks **************************************************/

int move_to(const FT_Vector* to, void* user) {
	printf("\tM %ld %ld\n", to->x, to->y);
	return 0;
}

int line_to(const FT_Vector* to, void* user) {
   	printf("\tL %ld %ld\n", to->x, to->y);
	return 0;
}

int conic_to(const FT_Vector* cp2, const FT_Vector* cp3, void* user) {
	printf("\tQ %ld %ld %ld %ld\n",
		cp2->x, cp2->y,
		cp3->x, cp3->y);
	return 0;
}


int cubic_to(const FT_Vector* cp2, const FT_Vector* cp3, const FT_Vector* cp4, void* user ) {
	printf("\tC %ld %ld %ld %ld %ld %ld\n",
		cp2->x, cp2->y,
		cp3->x, cp3->y,
		cp4->x, cp4->y);
	return 0;
}

/*
vim: ts=4 sw=4 noexpandtab nowrap
*/
