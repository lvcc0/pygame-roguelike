def list_connect(*lists):
    res = [[]]
    for i in range(max([len(lst) for lst in lists])):
        res.append([])
        for lst in lists:
            if i < len(lst):
                res[i] += lst[i]

    return res
