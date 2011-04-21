/* ex: set ts=8 noet: */
/*
 * Copyright 2011 Ryan Flynn <parseerror+github@gmail.com>
 *
 * our 3-ary ngrams are in binary format in ngram3.bin
 */

#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <arpa/inet.h>
#include "ngram3bin.h"

void ngram3bin_str(const struct ngram3map m, FILE *f)
{
	fprintf(f, "ngram3map(size=%llu)", m.size);
}

struct ngram3map ngram3bin_init(const char *path)
{
	struct stat st;
	struct ngram3map m = { NULL, -1, 0 };
	if (!stat(path, &st))
	{
		//printf("stat(\"%s\") size=%llu\n", path, (unsigned long long)st.st_size);
		if (-1 != (m.fd = open(path, O_RDONLY)))
		{
			m.size = st.st_size;
			m.m = mmap(NULL,m.size, PROT_READ, MAP_SHARED, m.fd, 0);
			if (MAP_FAILED == m.m)
			{
				perror("mmap");
				m.m = NULL;
			}
		}
	}
	return m;
}

// ng is 'cnt' items long; we need to ensure at least 1 more ngram3 in it
ngram3 * ngram3_find_spacefor1more(ngram3 *ng, unsigned long cnt)
{
	// allocate space for results on every power of 2
	// 0->1, 1->2, 2->4, 4->8, etc.
	if ((cnt & (cnt - 1)) == 0)
	{
		unsigned long alloc = cnt ? cnt * 2 : 1;
		ngram3 *tmp = realloc(ng, alloc * sizeof *ng);
		if (tmp)
		{
			ng = tmp;
		}
		else
		{
			free(ng);
			ng = NULL;
		}
	}
	return ng;
}

/*
 * map contains the mmap'ed contents of a dictionary file
 * the dictionary file is a list of variable-length entries in the form
 * [uint32_t id][uint32_t len][utf-8 encoded string of bytes length 'len']
 */
struct ngramword ngramword_load(const struct ngram3map m)
{
	struct ngramword w;
#	pragma pack(push, 1)
	struct cursor {
		uint32_t id;
		uint32_t len;
	}
	*cursor = m.m,
	*end = (void *)((char *)m.m + m.size);
#	pragma pack(pop)
	unsigned long long maxpossible = m.size / 6 + 1;
	w.word = calloc(maxpossible, sizeof *w.word);
	w.cnt = 0;
	while (cursor < end)
	{
		const char *str = (void *)((char *)cursor + sizeof *cursor);
		w.word[cursor->id].len = cursor->len;
		w.word[cursor->id].str = str;
#if 0
		if (w.cnt < 10)
			printf("cursor(id=%lu len=%u) buf=\"%.*s\"\n",
				(unsigned long)cursor->id, (unsigned)cursor->len,
				(unsigned)cursor->len, w.word[cursor->id].str);
#endif
		cursor = (void *)((char *)str + (cursor->len + (1 + (cursor->len+1) % 4)));
		w.cnt++;
	}
	w.word = realloc(w.word, w.cnt * sizeof *w.word);
	return w;
}

/*
 * FIXME: O(n)
 */
const unsigned long ngramword_word2id(const char *word, unsigned len, const struct ngramword w)
{
	unsigned long id = 0;
	printf("ngramword_word2id(word=\"%s\", w={%lu,%p})\n", word, w.cnt, w.word);
	while (id < w.cnt)
	{
		if (w.word[id].len == len && 0 == memcmp(word, w.word[id].str, len))
			break;
		id++;
	}
	if (id == w.cnt)
		id = 0;
	return id;
}

const char * ngramword_id2word(unsigned long id, const struct ngramword w)
{
	if (id < w.cnt)
		return w.word[id].str;
	return NULL;
}

void ngramword_fini(struct ngramword w)
{
	free(w.word);
}

/*
 * given an id 3-gram (x,y,z) and a list of ngram frequencies, count the number
 * of matches of (_,y,z) or (x,_,z) or (x,y,_)
 */
ngram3 * ngram3bin_find(ngram3 find, const struct ngram3map m)
{
	unsigned long ngcnt = 0;
	const ngram3 *end = (ngram3*)((char*)m.m + m.size);
	ngram3 *cur = m.m;
	ngram3 *res = NULL;
	/* convert ids to little endian */
	find.id[0] = htonl(htonl(find.id[0]));
	find.id[1] = htonl(htonl(find.id[1]));
	find.id[2] = htonl(htonl(find.id[2]));
	while (cur != end)
	{
		if (((cur->id[0] == find.id[0]) +
		     (cur->id[1] == find.id[1]) +
		     (cur->id[2] == find.id[2])) == 2)
		{
			res = ngram3_find_spacefor1more(res, ngcnt);
			if (!res)
				break;
			res[ngcnt] = *cur; /* copy result */
			ngcnt++;
		}
		cur++;
	}
	if (res)
	{
		res = ngram3_find_spacefor1more(res, ngcnt);
		if (res)
			res[ngcnt].freq = 0; // sentinel
	}
	return res;
}

void ngram3bin_fini(struct ngram3map m)
{
	munmap(m.m, m.size);
	close(m.fd);
}

#ifdef TEST

int main(void)
{
	const char *path = "ngram3.bin";
	struct ngram3map m = ngram3bin_init(path);
	const ngram3 find = { 5, 6, 7, 0 };
	printf("map %llu bytes (%llu ngram3s)\n", m.size, m.size / sizeof find);
	ngram3bin_find(find, m);
	ngram3bin_fini(m);
	return 0;
}

#endif

