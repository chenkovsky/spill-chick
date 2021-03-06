/* ex: set ts=8 noet: */
/*
 * Copyright 2011 Ryan Flynn <parseerror+github@gmail.com>
 */

#ifndef NGRAM3BIN_H
#define NGRAM3BIN_H

#include <stdio.h>
#include <stdint.h>

#define UNKNOWN_ID (0)
#define IMPOSSIBLE_ID (~0)

struct ngram3map
{
	void *m;
	int fd;
	unsigned long long size;
};

#define ngram3map_start(map) ((ngram3*)((map)->m))
#define ngram3map_end(map) ((ngram3*)(((char *)((map)->m)) + (map)->size))

struct ngramword
{
	unsigned long cnt;
	struct wordlen {
		unsigned len;
		unsigned freq;
		const char *str;
	} *word;
};

#pragma pack(push, 1)
struct ngramwordcursor {
	uint32_t len;
};
#pragma pack(pop)
typedef struct ngramwordcursor ngramwordcursor;

#define ngramwordcursor_str(cur)  ((char *)(cur) + sizeof *(cur))
#define ngramwordcursor_next(cur) (void *)((char *)(ngramwordcursor_str(cur) + ((cur)->len + (1 + ((cur)->len+1) % 4))))

#pragma pack(push, 1)
typedef struct
{
	uint32_t id[3],
		 freq;
} ngram3;
#pragma pack(pop)

/*
 * ngram3 is a sorted array of 3-grams (x,y,z)
 * for each unique x, count the number of sequential records (x,_,_)
 * this allows us to more efficiently search for (_,y,z)
 *
 * note: we don't need to track which id each span represents, we
 * can retrieve it when necessary; we just need the number of records
 */
typedef struct
{
	uint32_t *span;
} ngram3bin_index;

struct ngramword    ngramword_load(const struct ngram3map);
const unsigned long ngramword_word2id(const char *word, unsigned len, const struct ngramword);
const char *	    ngramword_id2word(unsigned long id, const struct ngramword);
void		    ngramword_totalfreqs(struct ngramword, const struct ngram3map *);
void		    ngramword_fini(struct ngramword);

struct ngram3map    ngram3bin_init(const char *path, int write);
unsigned long	    ngram3bin_freq(ngram3 find, const struct ngram3map *);
unsigned long	    ngram3bin_freq2(ngram3 find, const struct ngram3map *);
ngram3 *	    ngram3bin_like(ngram3 find, const struct ngram3map *);
ngram3 *	    ngram3bin_like_better(ngram3 find, const struct ngram3map *, ngram3bin_index *);
void		    ngram3bin_str (const struct ngram3map, FILE *);
void		    ngram3bin_fini(struct ngram3map);
ngram3 *	    ngram3bin_follows(const ngram3 *, const struct ngram3map *);

int		    ngram3bin_index_init(ngram3bin_index *, const struct ngram3map *, const struct ngramword *);
void		    ngram3bin_index_fini(ngram3bin_index *);

int ngram3cmp(const void *, const void *);

#endif /* NGRAM3BIN_H */

