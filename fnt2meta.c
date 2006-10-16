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
 * pulic domain
 * last update: 16.10.2006
 */

#include <stdio.h>
#include <string.h>
#include <math.h>

#include <ft2build.h>
#include FT_FREETYPE_H

int move_to(const FT_Vector*, void*);
int line_to(const FT_Vector*, void*);
int conic_to(const FT_Vector*, const FT_Vector*, void*);
int cubic_to(const FT_Vector*, const FT_Vector*, const FT_Vector*, void*);

#define MAX_GLYPH_NAME 256

int main(int argc, char** argv) {
	FT_Library	library;
	FT_Face		face;
	FT_Error	error;
	FT_Outline_Funcs funcs;
	
	long int i;
	char glyphname[MAX_GLYPH_NAME];

	if (argc < 2)
		/* not enought arguments */
		return 1;

	error = FT_Init_FreeType(&library);
	if (error)
		return 1;

	error = FT_New_Face(library, argv[1], 0, &face);
	if (error)
		return 1;

	/* process only fonts that defines glyph names */
	if (FT_HAS_GLYPH_NAMES(face)) {
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
			if (error)
				/* just skip glyph if error */
				continue;

			error = FT_Get_Glyph_Name(face, i, (FT_Pointer)glyphname, MAX_GLYPH_NAME);
			if (error)
				continue;

			/* display font name */
			printf("char %s\n", glyphname);
			

			/* display horiz andvance x */
			printf("\tadv %ld\n", face->glyph->metrics.horiAdvance);

			error = FT_Outline_Decompose(&(face->glyph->outline), &funcs, NULL);
			printf("end\n");
		}
		FT_Done_Face(face);
		FT_Done_FreeType(library);
		return 0;
	}
	else {
		FT_Done_Face(face);
		FT_Done_FreeType(library);
		return 1;
	}
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
